import yaml
from enum import IntEnum
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape
import markdown
import re

class SecLvl(IntEnum):
    POLY = 0
    SUBEXP = 1
    EXP = 2
    UNB = 10

    def __str__(self):
        return { 0:'poly', 1:'subexp', 2:'exp', 10:'unbounded' }[self.value]

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
            return f'<input type="checkbox" name="comment-checkbox" id="comment-{table}-{self.props["id"]}-checkbox">'
        return "-"

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
    
class Attack(Entry):
    header = """
    <tr class="header-row">
      <th>Name</th>
      <th>Complexity</th>
      <th>Quantum?</th>
      <th>Reference</th>
      <th>Comment</th>
    </tr>
    """
    template = Template("""
    <tr id="attack-{{ id }}"
        class="quantum-{{ quantum | default(false) }}
        complexity">
    <td class="name">{{ this.name() }}</td>
    <td class="complexity {{ complexity }}">{{ this.complexity() }}</td>
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
        return { 'poly': SecLvl.POLY,
                 'subexp': SecLvl.SUBEXP,
                 'exp': SecLvl.EXP }[self.props['complexity']]

class Trivial(Attack):
    def __init__(self):
        self.id = 'trivial'
        
    def complexity(self):
        return SecLvl.UNB
trivial = Trivial()
    
class Assumption(Entry):
    header = """
    <tr>
      <th>Name</th>
      <th>Classical Security</th>
      <th>Quantum Security</th>
      <th>Reference</th>
      <th>Comment</th>
    </tr>
    """
    template = Template("""
    <tr id="assumption-{{ id }}">
    <td class="name">{{ this.name() }}</td>
    <td class="c_sec complexity {{ this.security(False) }}">
    <a href="#attack-{{ this.best_attack(False).props.id }}"
       title="{{ this.best_attack(False).props.name.long }}">{{ this.security(False) }}</a>
    </td>
    <td class="q_sec complexity {{ this.security() }}">
    <a href="#attack-{{ this.best_attack().props.id }}"
       title="{{ this.best_attack().props.name.long }}">{{ this.security() }}</a>
    </td>
    <td class="reference">{{ this.reference() }}</td>
    <td class="comment-checkbox">{{ this.comment_checkbox("assumption") }}</td>
    </tr>
    <tr id="comment-assumption-{{ id }}" class="hidden-row">
        <td colspan="5" class="comment-cell"><h4>Comment</h4>{{this.comment()}}</td>
    </tr>
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

class Scheme(Entry):
    header = """
    <tr>
      <th>Name</th>
      <th>Type</th>
      <th>Classical Security</th>
      <th>Quantum Security</th>
      <th>Reference</th>
      <th>Comment</th>
    </tr>
    """
    template = Template("""
    <tr id="scheme-{{ id }}">
    <td class="name">{{ this.name() }}</td>
    <td class="type">{{ this.format_type() }}</td>
    <td class="c_sec complexity {{ this.security(False) }}">
    <a href="#attack-{{ this.best_attack(False).props.id }}"
       title="{{ this.best_attack(False).props.name.long }}">{{ this.security(False) }}</a>
    </td>
    <td class="q_sec complexity {{ this.security() }}">
    <a href="#attack-{{ this.best_attack().props.id }}"
       title="{{ this.best_attack().props.name.long }}">{{ this.security() }}</a>
    </td>
    <td class="reference">{{ this.reference() }}</td>
    <td class="comment-checkbox">{{ this.comment_checkbox("scheme") }}</td>
    </tr>
    <tr id="comment-scheme-{{ id }}" class="hidden-row">
        <td colspan="6" class="comment-cell"><h4>Comment</h4>{{this.comment()}}</td>
    </tr>
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

    
with open('attacks.yml') as att:
    with open('assumptions.yml') as ass:
        with open('schemes.yml') as sch:
            attacks = { id : Attack(id, props)
                        for (id, props) in yaml.safe_load(att).items() }
            assumptions = { id : Assumption(id, props)
                             for (id, props) in yaml.safe_load(ass).items() }
            schemes = { id : Scheme(id, props)
                        for (id, props) in yaml.safe_load(sch).items() }
            
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
