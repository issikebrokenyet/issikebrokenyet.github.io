import yaml
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape
from fractions import Fraction
import markdown
import re
from functools import cached_property, cache
import inspect

class L:
    """
    Complexity function L(a,c) = exp( (c+o(1)) (log n)^a (loglog n)^(1-a) )
    """
    def __init__(self, a, c=None):
        f = lambda n: (n is None and float('inf')
                       or type(n) == str and ('.' in n and float(n) or Fraction(n))
                       or n)
        self.a = f(a)
        self.c = f(c)

    @classmethod
    def parse(cls, str):
        m = re.match(r'poly(\((\d+([./]\d+)?)\))?$', str)
        if m:
            return cls(0, m.group(2))
        m = re.match(r'L\((\d+([./]\d+)?)(,(\d+([./]\d+)?))?\)$', str)
        if m:
            return cls(m.group(1), m.group(4))
        m = re.match(r'exp(\((\d+([./]\d+)?)\))?$', str)
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
        elif self.a < 1:
            return 'subexp'
        else:
            return 'exp'

#--------------------#
# Some utility stuff #
#--------------------#

class NestedDict(dict):
    'A utility class to easily access subvariants'
    def __getitem__(self, key):
        if ">" in key:
            parent, variant = key.split(">", maxsplit=1)
            return self[parent].props["variants"][variant]
        else:
            return super().__getitem__(key)

def norecloop(default=None):
    'A decorator to break out of recursion loops for methods (based on self)'
    def decorator(met):
        def wrapper(self, *args, **kwds):
            stack = inspect.stack()
            current = stack.pop(0)
            frames = [inspect.getargvalues(s.frame)
                      for s in stack if s.function == current.function]
            if any(f.locals['self'] is self for f in frames):
                return default
            else:
                return met(self, *args, **kwds)

        return wrapper

    return decorator
    
#----------------------------------#
# Main Class for Rows in our table #
#----------------------------------#

class Entry:
    def __init__(self, id, props, parent=None):
        self.parent = parent
        self.props = props
        self.props["id"] = id
        self.props["this"] = self
        if "variants" in self.props:
            self.props["variants"] = NestedDict({
                var: self.__class__(var, props, self)
                for var, props in self.props["variants"].items()
            })
            
    def __repr__(self):
        return self.template.render(self.props)

    @cached_property
    def longid(self):
        return (self.parent.longid + '>' if self.parent else '') + self.props["id"]
    
    @cached_property
    def name(self):
        if self.props['name'].get('long') and self.props['name'].get('short'):
            return f'<abbr title="{ self.props["name"]["long"] }">{ self.props["name"]["short"] }</abbr>'
        else:
            return self.props['name'].get('short') or self.props['name'].get('long')

    @cached_property
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
            input_ele = f'<input type="checkbox" name="comment-checkbox" id="comment-{table}:{self.longid}!checkbox">'
            label_ele = f'<label for="comment-{table}:{self.longid}!checkbox">Comments</label>'
            return f"{input_ele}\n{label_ele}"
        return "-"

    def variant_checkbox(self, table):
        if self.props.get("variants"):
            input_ele =  f'<input type="checkbox" name="variant-checkbox" id="variant-{table}:{self.longid}!checkbox">'
            label_ele = f'<label for="variant-{table}:{self.longid}!checkbox">Variants</label>'
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

    @cached_property
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
    <tr id="attack:{{ this.longid }}"
        class="quantum-{{ quantum | default(false) }}
        complexity">
    <td class="name">{{ this.name }}</td>
    <td class="complexity {{ this.complexity.simple() }}">{{ this.complexity }}</td>
    <td class="quantum">{% if quantum %}Yes{% else %}No{% endif %}</td>
    <td class="reference">{{ this.reference }}</td>
    <td class="comment-checkbox">{{ this.comment_checkbox("attack") }}</td>
    </tr>
    <tr id="comment-attack:{{ this.longid }}" class="hidden-row">
        <td colspan="5" class="comment-cell"><h4>Comment</h4>{{this.comment}}</td>
    </tr>
    """)

    @property
    def quantum(self):
        return self.props.get("quantum", False)

    @cached_property
    def complexity(self):
        return L.parse(self.props['complexity'])    

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
    <tr id="assumption:{{ this.longid }}"
        {% if this.parent %} class="hidden-row variant-row
            variant-assumption:{{ this.parent.longid }}" {% endif %}>
        <td class="name">{{ this.name }}</td>
        <td class="c_sec complexity {{ this.security(False).simple() }}">
        <a href="#attack:{{ this.best_attack(False).longid }}"
           title="{{ this.best_attack(False).props.name.long }}">{{ this.security(False) }}</a>
        </td>
        <td class="q_sec complexity {{ this.security().simple() }}">
        <a href="#attack:{{ this.best_attack().longid }}"
           title="{{ this.best_attack().props.name.long }}">{{ this.security() }}</a>
        </td>
        <td class="reference">{{ this.reference }}</td>
        <td class="checkboxes">
            {{ this.comment_checkbox("assumption") }}
            {{ this.variant_checkbox("assumption") }}
        </td>
    </tr>
    <tr id="comment-assumption:{{ this.longid }}" class="hidden-row">
        <td colspan="5" class="comment-cell"><h4>Comment</h4>{{this.comment}}</td>
    </tr>
    {% if this.props.variants %}
        {% for variant in this.props.variants.values() %}
            {{ variant }}
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
        if 'variants' in self.props:
            for variant in self.props["variants"].values():
                variant.link(assumptions, attacks)

    @norecloop([])
#    @cache
    def attacks(self, quantum=True):
        # Any attack on parent is also an attack on us
        attacks = self.parent.attacks(quantum) if self.parent is not None else []
        # Attacks explicitly listed
        attacks += [a for a in self.props.get('attacks', []) if not a.quantum or quantum]
        # Attacks on weaker assumptions are attacks on us
        for a in self.props.get('reduces_to', []):
            attacks += a.attacks(quantum)
        # todo: handle quantum reductions
        #
        # And now the most controversial one:
        # if the parent has a generic reduction, specialize it
        # (assumes a single level of nesting)
        #
        # todo: why does this break caching?
        if self.parent is not None:
            for a in self.parent.props.get('reduces_to', []):
                sibling = a.props.get('variants', dict()).get(self.props['id'])
                if sibling:
                    attacks += sibling.attacks(quantum)

        return attacks
        

    def best_attack(self, quantum=True):
        return min(self.attacks(quantum),
                   key=lambda a: a.complexity)
        
    def security(self, quantum=True):
        return self.best_attack(quantum).complexity

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
    <tr id="scheme:{{ this.longid }}"
        {% if this.parent %} class="hidden-row variant-row
            variant-scheme:{{ this.parent.longid }}" {% endif %}>
        <td class="name">{{ this.name }}</td>
        <td class="type">{{ this.format_type() }}</td>
        <td class="c_sec complexity {{ this.security(False).simple() }}">
        <a href="#attack:{{ this.best_attack(False).longid }}"
           title="{{ this.best_attack(False).props.name.long }}">{{ this.security(False) }}</a>
        </td>
        <td class="q_sec complexity {{ this.security().simple() }}">
        <a href="#attack:{{ this.best_attack().longid }}"
           title="{{ this.best_attack().props.name.long }}">{{ this.security() }}</a>
        </td>
        <td class="reference">{{ this.reference }}</td>
        <td class="checkboxes">
            {{ this.comment_checkbox("scheme") }}
            {{ this.variant_checkbox("scheme") }}
        </td>
    </tr>
    <tr id="comment-scheme:{{ this.longid }}" class="hidden-row">
        <td colspan="6" class="comment-cell"><h4>Comment</h4>{{this.comment}}</td>
    </tr>
    {% if this.props.variants %}
        {% for variant in this.props.variants.values() %}
            {{ variant }}
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
        if 'variants' in self.props:
            for variant in self.props["variants"].values():
                variant.link(assumptions)

    def best_attack(self, quantum=True):
        return min((a.best_attack(quantum)
                    for a in self.props['assumptions']),
                   key = lambda a: a.complexity)

    def security(self, quantum=True):
        return self.best_attack(quantum).complexity

    def format_type(self):
        type_data = self.props['type']
        if isinstance(type_data, list):
            return ", ".join(type_data)
        return type_data

#-----------------------------#
# Logic to build the template #
#-----------------------------#
    
with open('attacks.yml') as att:
    with open('assumptions.yml') as ass:
        with open('schemes.yml') as sch:
            attacks = NestedDict({ id : Attack(id, props)
                                   for (id, props) in yaml.safe_load(att).items() })
            assumptions =  NestedDict({ id : Assumption(id, props)
                                        for (id, props) in yaml.safe_load(ass).items() })
            schemes =  NestedDict({ id : Scheme(id, props)
                                    for (id, props) in yaml.safe_load(sch).items() })
            
            for a in assumptions.values():
                a.link(assumptions, attacks)
            
            for s in schemes.values():
                s.link(assumptions)
                
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
