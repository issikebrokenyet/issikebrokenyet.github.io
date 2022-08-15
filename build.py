import yaml
from enum import IntEnum
from jinja2 import Template

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
    
class Attack(Entry):
    header = """
    <tr>
      <th>Name</th>
      <th>Complexity</th>
      <th>Quantum?</th>
    </tr>
    """
    template = Template("""
    <tr id="{{ id }}"
        class="quantum-{{ quantum | default(false) }}
        complexity-{{ complexity }}">
    <td class="name">{{ this.name() }}</td>
    <td class="complexity">{{ this.complexity() }}</td>
    <td class="quantum">{% if quantum %}yes{% else %}no{% endif %}</td>
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
    </tr>
    """
    template = Template("""
    <tr id="{{ id }}">
    <td class="name">{{ this.name() }}</td>
    <td class="c_sec complexity-{{ this.security(False) }}">
    <a href="#{{ this.best_attack(False).props.id }}"
       title="{{ this.best_attack(False).props.name.long }}">{{ this.security(False) }}</a>
    </td>
    <td class="q_sec complexity-{{ this.security() }}">
    <a href="#{{ this.best_attack().props.id }}"
       title="{{ this.best_attack().props.name.long }}">{{ this.security() }}</a>
    </td>
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
    </tr>
    """
    template = Template("""
    <tr id="{{ id }}">
    <td class="name">{{ this.name() }}</td>
    <td class="type">{{ type }}</td>
    <td class="c_sec complexity-{{ this.security(False) }}">
    <a href="#{{ this.best_attack(False).props.id }}"
       title="{{ this.best_attack(False).props.name.long }}">{{ this.security(False) }}</a>
    </td>
    <td class="q_sec complexity-{{ this.security() }}">
    <a href="#{{ this.best_attack().props.id }}"
       title="{{ this.best_attack().props.name.long }}">{{ this.security() }}</a>
    </td>
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

            print("""
            <!Doctype html>
            <html>
            <head>
              <title>Is SIKE broken yet?</title>
              <meta name="description"
                    content="A knowledge base of most isogeny based cryptosystem and the best attacks on them." />
              <link rel="stylesheet" href="style.css" />
            </head>
            <body>
              <h1>Is SIKE broken yet?</h1>
              <h2 id="schemes">Schemes</h2>
              <table>
              <thead>
              %s
              </thead>
              <tbody>
              %s
              </tbody>
              </table>
              <h2 id="assumptions">Assumptions</h2>
              <table>
              <thead>
              %s
              </thead>
              <tbody>
              %s
              </tbody>
              </table>
              <h2 id="attacks">Attacks</h2>
              <table>
              <thead>
              %s
              </thead>
              <tbody>
              %s
              </tbody>
              </table>
              <footer>
                <a href="https://github.com/issikebrokenyet/issikebrokenyet.github.io/">Contribute on GitHub</a>
              </footer>
            </body>
            </html>
            """ % (
                Scheme.header,
                "\n".join(repr(a) for a in schemes.values()),
                Assumption.header,
                "\n".join(repr(a) for a in assumptions.values()),
                Attack.header,
                "\n".join(repr(a) for a in attacks.values())
            ))
