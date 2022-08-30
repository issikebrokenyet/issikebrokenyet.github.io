# Is SIKE Broken Yet?

<https://issikebrokenyet.github.io>

A knowledge base of most isogeny based cryptosystems and the best attacks on them.

---

## What? Why?

The summer of 2022 will forever remain impressed in the memories of
cryptographers. Four post-quantum schemes were [selected by NIST for
standardization](https://csrc.nist.gov/News/2022/pqc-candidates-to-be-standardized-and-round-4),
Rainbow was broken [in a weekend on a
laptop](https://eprint.iacr.org/2022/214), and
[SIKE](https://eprint.iacr.org/2022/975)
[was](https://eprint.iacr.org/2022/1026)
[destroyed](https://eprint.iacr.org/2022/1038).

Following the spectacular break on SIKE, a lot of confusion ensued on
how much of isogeny based crypto is left alive, if any at all.  The
purpose of this knowledge base is to keep track of most, if not all,
isogeny based **schemes**, **assumptions** and **attacks**, so to
provide a complete picture of which directions in isogeny based
cryptography are still viable.


## Contributing: Cryptography

The knowledge base consists of three [YAML](https://yaml.org/) files,
easy to read and to edit: [`schemes.yml`](schemes.yml),
[`assumptions.yml`](assumptions.yml) and
[`attacks.yml`](attacks.yml). To add a scheme, assumption or attack,
simply edit those files and create a pull request.

Please adhere to the following data model:

```yaml
### `schemes.yml`

# A short lowercase identifier for the scheme. Must be unique.
sidh:

  # The scheme must have at least one of a short or long form name
  name:
    short: SIDH
    long: Supersingular Isogeny Diffie-Hellman

  # What kind of crypto primitive is this?
  type: Key Exchange
  
  # What security assumptions does it reduce to?
  # Use identifiers in `assumptions.yml`.
  # 
  # If you put more than one assumption, that's understood as an AND:
  # the scheme is broken if any of the assumptions is broken.
  # Try to keep this list minimal, and rely on `assumptions.yml`
  # for reductions between assumptions
  assumptions:
    - sidh

  # What paper(s) describe the scheme?
  # Format is `Label: link`. Use permalinks.
  references:
    JDF11: 'https://doi.org/10.1007/978-3-642-25405-5_2'
    DJP14: 'https://eprint.iacr.org/2011/506'

  # A Markdown field for extra comments. 
  # References in brackets are automatically expanded to links.
  comment: >-
    Fun fact: [JDF11] does not give a name to the scheme.

  # A dictionary of variants of the scheme above.
  # The keys of the variants need not be unique.
  # Each entry supports the same keys as the main entry.
  variants:
    random:
      name:
        long: SIDH with random starting curve
      type: Key Exchange
      assumptions:
        - cssi
      references:
        Pet17: 'https://eprint.iacr.org/2017/571'
        BB+22: 'https://eprint.iacr.org/2022/518'
      comment: >-
        Folklore version SIDH, starting from a random curve of unknown
        endomorphism ring.  First published mention in [Pet17],
        however it is currently not known how to generate such a curve
        without a trusted setup (see [BB+22]).
```

```yaml
### `assumptions.yml`

# A short lowercase identifier for the assumption. Must be unique.
vector:

  # The assumption must have at least one of a short or long form name
  name:
    long: Vectorization

  # Other names by which the assumption may be known
  aliases:
    - short: GAIP
      long: Group Action Inverse Problem

  # What attacks break the assumption.
  # Use identifiers in `attacks.yml`.
  # 
  # Try to keep this list minimal, and rely on reduces_to
  # for additional attacks that may break weaker assumptions.
  attacks:
    - kuperberg
    - galbraith

  # What weaker assumptions this assumption reduces to.
  # If any of these is broken, the assumption is broken.
  # Use identifiers in `assumptions.yml`.
  #
  # Reductions may contain only one subkey: `quantum`, stating whether the 
  # reduction uses a quantum algorithm.
  #
  # May refer to variants of an assumption using the syntax `parent>variant`.
  #
  # May contain circular references, in case some assumptions are equivalent.
  reduces_to:
    parallelization:
      quantum: yes

  # What paper(s) define the assumption?
  # Format is `Label: link`. Use permalinks.
  references:
    BY01: 'https://doi.org/10.1007/3-540-38424-3_7'
    Cou06: 'https://eprint.iacr.org/2006/291'
    Sto10: 'https://dx.doi.org/10.3934/amc.2010.4.215'
    GP+18: 'https://eprint.iacr.org/2018/1199'

  # A Markdown field for extra comments. 
  # References in brackets are automatically expanded to links.
  comment: >-
    Given two random elements x₀, x₁ in a set acted upon transitively
    by a group G, find an element of G that maps x₀ to x₁. By random
    self-reducibility, this is equivalent to the problem where x₀ is
    fixed.

  # A dictionary of variants of the assumption above.
  # These must be special instances of the parent assumption.
  # Link to them using the syntax `parent>variant`.
  # Each entry supports the same keys as the main entry.
  variants:
    ordinary:
      name:
        long: Vectorization (ordinary)
      comment: >-
        The variant where the set is a set of ordinary curves with
        endomorphism ring isomorphic to an order O, and the set is the
        class group of O.
    supersingular:
      name:
        long: Vectorization (supersingular)
      references:
        CL+18: 'https://eprint.iacr.org/2018/383'
        CPV19: 'https://eprint.iacr.org/2019/1202'
        Wes21: 'https://eprint.iacr.org/2021/1583'
      reduces_to:
        ssendringfp:
      comment: >-
        The variant where the set is a set of supersingular curves
        defined over a prime field $\mathbb{F}_p$, and the set is the
        class group Cl(√-p). The reduction to the Endomorphism ring
        problem over $\mathbb{F}_p$ was done in steps in [CPV19] and
        [Wes21].
```

```yaml
### `attacks.yml`

# A short lowercase identifier for the attack. Must be unique.
kuperberg:

  # The assumption must have at least one of a short or long form name
  name:
    long: Kuperberg
    
  # The complexity of the attack. 
  #
  # This is expressed as a value of the L(a,c) complexity function
  # <https://en.wikipedia.org/wiki/L-notation>. The second argument
  # is optional (if omitted, it is interpreted as unbounded in comparisons).
  #
  # Four short-hand syntaxes are also supported:
  # - poly: shortcut for L(0)
  # - poly(c): shortcut for L(0,c)
  # - exp: shortcut for L(1)
  # - exp(a): shortcut for L(1,a)
  complexity: L(1/2)
  
  # Whether this is a quantum attack
  quantum: yes
  
  # What paper(s) describe the attack?
  # Format is `Label: link`. Use permalinks.
  references:
    Kup04: "https://arxiv.org/abs/quant-ph/0302112"
    CJS13: "https://doi.org/10.1515/jmc-2012-0016"

  # A Markdown field for extra comments. 
  # References in brackets are automatically expanded to links.
  comment: >-
    [Kup04] describes a generic quantum algorithm to solve the hidden
    shift problem (equivalently, the dihedral hidden subgroup
    problem). [CJS13] uses Kuperberg's algorithm as a subroutine to
    attack the vectorization problem.
```

If all this looks too complicated, but you still want to suggest
adding a scheme, assumption or attack, [create an issue](issues).
Also create an issue if you want to suggest additions to the data
model.

### On variants

Schemes and assumptions support *variants*. A variant `var` of a
scheme/assumption `par` gets the id `par>var`, which can be used for
URLs (`#par>var`), and for linking in `assumptions:` and
`reduces_to:`.

While scheme variants are just a way to lump several schemes together
for readability (e.g., by displaying a foldable row in a table), the
semantic of assumption variants is quite involved.

**A variant of an assumption is always a special case of the main
assumption.** So, for example, `vector>supersingular` is the special
case of `vector` for the group action of Frobenius on supersingular
curves. Hence, whatever `vector` reduces to, `vector>supersingular`
also reduces to.

Additionally, if `vector` reduces to `parallelization`, then
`vector>supersingular` automatically reduces to
`parallelization>supersingular`, without the need to explicitly type
the reduction. 

Both rules save quite some typing when entering complex networks of
assumptions with several variants, but require some care.

We encourage to use variants of schemes sparingly, only to lump
together minor variants that appear seldom in the litterature.  We
encourage, instead, to make liberal use of assumption variants, as
this simplifies quite a lot the knowledge base management.

**Note:** at the moment, only one level of nesting is permitted in
variants.


## Contributing: WebDev

The website is generated by a Python script.  We are open on
technologies, if you want to suggest improvements, but we like to keep
it simple. We would also like to encourage experiments with completely
different UIs.

The build scripts are in [`src/`](src/), the static files are in
[`_site/`](_site/) and the HTML templates in
[`templates/`](templates/).  The easiest way to setup the environment
and to build the site is by using `make`.

```
# Setup the Python virtual environment
make venv

# Make the website
make

# Continuosly make when a file change (Linux only)
make watch
```

Or simply run `make`.
