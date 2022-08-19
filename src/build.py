import yaml
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape
from fractions import Fraction
import markdown
import re

class L:
    """
    Complexity function L(a,c) = exp( (c+o(1)) (log n)^a (loglog n)^(1-a) )
    """
    def __init__(self, a, c=None):
        self.a = Fraction(a)
        self.c = Fraction(c) if c is not None else float('inf')

    @classmethod
    def parse(cls, str):
        m = re.match(r'poly(\(([\d/]+)\))?$', str)
        if m:
            return cls(0, m.group(2))
        m = re.match(r'L\(([\d/]+)(,([\d/]+))?\)$', str)
        if m:
            return cls(m.group(1), m.group(3))
        m = re.match(r'exp(\(([\d/]+)\))?$', str)
        if m:
            return cls(1, m.group(2))
        raise RuntimeError('Cannot parse %s as a complexity' % str)
        
    def __lt__(self, other):
        return self.a < other.a or self.a == other.a and self.c < other.c
    
    def __str__(self):
        if self.a == 0:
            if self.c == 1:
                return 'Õ(n)'
            elif self.c < float('inf'):
                return 'Õ(n<sup>%s</sup>)' % self.c
            else:
                return 'poly'
        elif self.a == 1:
            if self.c == 1:
                return 'exp(n)'
            elif self.c < float('inf'):
                return 'exp(n)<sup>%s</sup>' % self.c
            else:
                return 'exp'
        else:
            if self.c < float('inf'):
                return 'L(%s, %s)' % (self.a, self.c)
            else:
                return 'L(%s)' % self.a

    def simple(self):
        if self.a == 0:
            return 'poly'
        elif self.a == 1:
            return 'exp'
        else:
            return 'subexp'

#----------------------------------#
# Main Class for Rows in our table #
#----------------------------------#

class Entry:
    def __init__(self, id, props):
        self.props = props
        self.props["id"] = id
        self.props["this"] = self

    def __repr__(self):
        return self.template.render(self.props)

    def name(self):
        if self.props['name'].get('long') and self.props['name'].get('short'):
            return f'<abbr title="{ self.props["name"]["long"] }">{ self.props["name"]["short"] }</abbr>'
        else:
            return self.props['name'].get('short') or self.props['name'].get('long')

    def reference(self):
        links = []
        reference_dict = self.props.get("references", {})

        for slug, url in reference_dict.items():
            link = f'<a class="reference-link" href="{url}" target="_blank">{slug}</a>'
            links.append(link)
        if links:
            return " ".join(links)
        return "-"

    def comment_checkbox(self, table):
        if self.props.get("comment"):
            input_ele = f'<input type="checkbox" name="comment-checkbox" id="comment-{table}-{self.props["id"]}-checkbox">'
            label_ele = f'<label for="comment-{table}-{self.props["id"]}-checkbox"><span class="chevron">&#x25B8;</span>&nbsp;Comments</label>'
            return f"{input_ele}\n{label_ele}"
        return "-"

    def variant_checkbox(self, table):
        if self.props.get("variants"):
            input_ele =  f'<input type="checkbox" name="variant-checkbox" id="variant-{table}-{self.props["id"]}-checkbox">'
            label_ele = f'<label for="variant-{table}-{self.props["id"]}-checkbox"><span class="chevron">&#x25B8;</span>&nbsp;Variants</label>'
            return f"<br>{input_ele}\n{label_ele}"
        return ""

    def reference_in_comment(self, comment):
        # Collect the element's references
        ref_dict = self.props.get("references", {})
        comment_references = re.findall(r"\[(.*?)\]", comment)
        # I don't want recursive replacement, so focus on unique
        # matches...
        comment_references = list(set(comment_references))
        for ref in comment_references:
            if ref in ref_dict:
                anchor = f'<a class="reference-link" href="{ref_dict[ref]}" target="_blank">[{ref}]</a>'
                comment = comment.replace(f"[{ref}]", anchor)
        return comment

    def comment(self):
        comment_markdown = self.props.get("comment", "").rstrip()
        comment_html =  markdown.markdown(comment_markdown, 
                                 extensions=["nl2br"])
        return self.reference_in_comment(comment_html)

#-------------------#
# Logic for Attacks #
#-------------------#

class Attack(Entry):
    header = """
    <tr class="header-row">
      <th>Name</th>
      <th>Complexity</th>
      <th>Quantum?</th>
      <th>Reference</th>
      <th>Additional Information</th>
    </tr>
    """
    template = Template("""
    <tr id="attack-{{ id }}"
        class="quantum-{{ quantum | default(false) }}
        complexity">
    <td class="name">{{ this.name() }}</td>
    <td class="complexity {{ this.complexity().simple() }}">{{ this.complexity() }}</td>
    <td class="quantum">{% if quantum %}Yes{% else %}No{% endif %}</td>
    <td class="reference">{{ this.reference() }}</td>
    <td class="comment-checkbox">{{ this.comment_checkbox("attack") }}</td>
    </tr>
    <tr id="comment-attack-{{ id }}" class="hidden-row">
        <td colspan="5" class="comment-cell"><h4>Comment</h4>{{this.comment()}}</td>
    </tr>
    """)

    def quantum(self):
        return self.props.get("quantum", False)

    def complexity(self):
        return L.parse(self.props['complexity'])

class Trivial(Attack):
    def __init__(self):
        self.id = 'trivial'
        
    def complexity(self):
        return L(10)
trivial = Trivial()
    

#----------------------------------------------#
# Logic for Assumption and Assumption variants #
#----------------------------------------------#

class Assumption(Entry):
    """
    The extra hidden rows are for CSS nonsense.
    Another option would be to use JS to change classes
    but I really want as little JS as possible...

    Basically, the problem is:

    We can select nth-elements, but we can't count
    only elements with a certain class, so when we
    have an odd number of variants, the odd/even
    color highlight gets an off by one error...

    This is done in Schemes too
    """
    header = """
    <tr>
      <th>Name</th>
      <th>Classical Security</th>
      <th>Quantum Security</th>
      <th>Reference</th>
      <th>Additional Information</th>
    </tr>
    """
    template = Template("""
    <tr id="assumption-{{ id }}">
        <td class="name">{{ this.name() }}</td>
        <td class="c_sec complexity {{ this.security(False).simple() }}">
        <a href="#attack-{{ this.best_attack(False).props.id }}"
           title="{{ this.best_attack(False).props.name.long }}">{{ this.security(False) }}</a>
        </td>
        <td class="q_sec complexity {{ this.security().simple() }}">
        <a href="#attack-{{ this.best_attack().props.id }}"
           title="{{ this.best_attack().props.name.long }}">{{ this.security() }}</a>
        </td>
        <td class="reference">{{ this.reference() }}</td>
        <td class="checkboxes">
            {{ this.comment_checkbox("assumption") }}
            {{ this.variant_checkbox("assumption") }}
        </td>
    </tr>
    <tr id="comment-assumption-{{ id }}" class="hidden-row">
        <td colspan="5" class="comment-cell"><h4>Comment</h4>{{this.comment()}}</td>
    </tr>
    {% if this.props.variants %}
        {% for variant, props in this.props.variants.items() %}
            {{ this.get_variant(variant, props, id) }}
        {% endfor%}
    {% endif%}
    {% if this.props.variants|length % 2 == 1 %}
        <tr class="hidden-row"><td colspan="5"></td></tr>
        <tr class="hidden-row"><td colspan="5"></td></tr>
    {% endif %}
    """)

    def link(self, assumptions, attacks):
        if 'attacks' in self.props:
            self.props['attacks'] = [attacks[a]
                                     for a in self.props['attacks']]
        if 'reduces_to' in self.props:
            self.props['reduces_to'] = [assumptions[a]
                                        for a in self.props['reduces_to']]

    def best_attack(self, quantum=True, excl=None):
        ba1 = min((a
                   for a in self.props.get('attacks', [])
                   if not a.quantum() or quantum),
                  key=lambda a: a.complexity(),
                  default=trivial)
        excl = ([] if excl is None else excl) + [self]
        ba2 = min((a.best_attack(quantum, excl)
                   for a in self.props.get('reduces_to', [])
                   if a not in excl),
                  key=lambda a: a.complexity(),
                  default=trivial)
        if ba1 is Trivial:
            return ba2
        elif ba2 is Trivial:
            return ba1
        else:
            return min([ba1, ba2], key=lambda a: a.complexity())
        
    def security(self, quantum=True):
        return self.best_attack(quantum).complexity()

    def get_variant(self, id, props, parent):
        return AssumptionVariant(id, props, parent)

class AssumptionVariant(Assumption):
    def __init__(self, id, props, parent):
        Assumption.__init__(self, id, props)
        self.parent = parent

    template = Template("""
    <tr id="variant-assumption-{{ this.parent }}-{{ id }}" class="hidden-row variant-row variant-assumption-{{ this.parent }}">
        <td class="name">{{ this.name() }}</td>
        <td class="c_sec complexity {{ this.security(False).simple() }} ">
        <a href="#attack-{{ this.best_attack(False).props.id }}"
           title="{{ this.best_attack(False).props.name.long }}">{{ this.security(False) }}</a>
        </td>
        <td class="q_sec complexity {{ this.security().simple() }}">
        <a href="#attack-{{ this.best_attack().props.id }}"
           title="{{ this.best_attack().props.name.long }}">{{ this.security() }}</a>
        </td>
        <td class="reference">{{ this.reference() }}</td>
        <td class="comment-checkbox">{{ this.comment_checkbox("assumption-" + this.parent) }}</td>
    </tr>
    <tr id="comment-assumption-{{ this.parent }}-{{ id }}" class="hidden-row">
        <td colspan="5" class="comment-cell"><h4>Comment</h4>{{this.comment()}}</td>
    </tr>
    """)

#---------------------------------------#
# Logic for Schemes and Scheme variants #
#---------------------------------------#

class Scheme(Entry):
    header = """
    <tr>
      <th>Name</th>
      <th>Type</th>
      <th>Classical Security</th>
      <th>Quantum Security</th>
      <th>Reference</th>
      <th>Additional Information</th>
    </tr>
    """
    template = Template("""
    <tr id="scheme-{{ id }}">
        <td class="name">{{ this.name() }}</td>
        <td class="type">{{ this.format_type() }}</td>
        <td class="c_sec complexity {{ this.security(False).simple() }}">
        <a href="#attack-{{ this.best_attack(False).props.id }}"
           title="{{ this.best_attack(False).props.name.long }}">{{ this.security(False) }}</a>
        </td>
        <td class="q_sec complexity {{ this.security().simple() }}">
        <a href="#attack-{{ this.best_attack().props.id }}"
           title="{{ this.best_attack().props.name.long }}">{{ this.security() }}</a>
        </td>
        <td class="reference">{{ this.reference() }}</td>
        <td class="checkboxes">
            {{ this.comment_checkbox("scheme") }}
            {{ this.variant_checkbox("scheme") }}
        </td>
    </tr>
    <tr id="comment-scheme-{{ id }}" class="hidden-row">
        <td colspan="6" class="comment-cell"><h4>Comment</h4>{{this.comment()}}</td>
    </tr>
    {% if this.props.variants %}
        {% for variant, props in this.props.variants.items() %}
            {{ this.get_variant(variant, props, id) }}
        {% endfor%}
    {% endif%}
    {% if this.props.variants|length % 2 == 1 %}
        <tr class="hidden-row"><td colspan="6"></td></tr>
        <tr class="hidden-row"><td colspan="6"></td></tr>
    {% endif %}
    """)

    def link(self, assumptions):
        self.props['assumptions'] = [assumptions[a]
                                     for a in self.props['assumptions']]

    def best_attack(self, quantum=True):
        return min((a.best_attack(quantum)
                    for a in self.props['assumptions']),
                   key = lambda a: a.complexity())

    def security(self, quantum=True):
        return self.best_attack(quantum).complexity()

    def format_type(self):
        type_data = self.props['type']
        if isinstance(type_data, list):
            return ", ".join(type_data)
        return type_data

    def get_variant(self, id, props, parent):
        return SchemeVariant(id, props, parent)

class SchemeVariant(Scheme):
    def __init__(self, id, props, parent):
        Scheme.__init__(self, id, props)
        self.parent = parent

    template = Template("""
    <tr id="variant-scheme-{{ this.parent }}-{{ id }}" class="hidden-row variant-row variant-scheme-{{ this.parent }}">
        <td class="name">{{ this.name() }}</td>
        <td class="type">{{ this.format_type() }}</td>
        <td class="c_sec complexity {{ this.security(False).simple() }}">
        <a href="#attack-{{ this.best_attack(False).props.id }}"
           title="{{ this.best_attack(False).props.name.long }}">{{ this.security(False) }}</a>
        </td>
        <td class="q_sec complexity {{ this.security().simple() }}">
        <a href="#attack-{{ this.best_attack().props.id }}"
           title="{{ this.best_attack().props.name.long }}">{{ this.security() }}</a>
        </td>
        <td class="reference">{{ this.reference() }}</td>
        <td class="comment-checkbox">{{ this.comment_checkbox("scheme-" + this.parent) }}</td>
    </tr>
    <tr id="comment-scheme-{{ this.parent }}-{{ id }}" class="hidden-row">
        <td colspan="6" class="comment-cell"><h4>Comment</h4>{{this.comment()}}</td>
    </tr>
    """)

#-----------------------------#
# Logic to build the template #
#-----------------------------#

def create_classes_from_yml(yml_data, ClassBase, ClassVariant):
    class_dict = {}
    class_variants_dict = {}
    for (id, props) in yaml.safe_load(yml_data).items():
        class_dict[id] = ClassBase(id, props)
        for (id_variant, props_variant) in props.get("variants", {}).items():
            class_variants_dict[id_variant] = ClassVariant(id_variant, props_variant, id)
    return class_dict, class_variants_dict
    
with open('attacks.yml') as att:
    with open('assumptions.yml') as ass:
        with open('schemes.yml') as sch:
            attacks = { id : Attack(id, props)
                        for (id, props) in yaml.safe_load(att).items() }

            # For the link, we now need to collect assumptions and variants
            # This code got longer, so I factored it out for reuse for other
            # Classes
            assumptions, assumptions_variants = create_classes_from_yml(ass, Assumption, AssumptionVariant)
            schemes, schemes_variants = create_classes_from_yml(sch, Scheme, SchemeVariant)
            
            for a in assumptions.values():
                a.link(assumptions, attacks)
            for av in assumptions_variants.values():
                av.link(assumptions, attacks)
            
            for s in schemes.values():
                s.link(assumptions)
            for sv in schemes_variants.values():
                sv.link(assumptions)

            env = Environment(
                loader = FileSystemLoader("templates"),
                autoescape=select_autoescape()
            )
            index = env.get_template("index.html")
            print(index.render(
                schemes_head=Scheme.header,
                schemes="\n".join(repr(a) for a in schemes.values()),
                assumptions_head=Assumption.header,
                assumptions="\n".join(repr(a) for a in assumptions.values()),
                attacks_head=Attack.header,
                attacks="\n".join(repr(a) for a in attacks.values())
            ))
