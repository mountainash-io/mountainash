Can you analyse our code base and come up with a plan for creating a well organised set of unit tests.
  The tests:
  - Must be real tests. NO MOCK TESTS OR FIXTURES.
  - Cover the full suite of orthogonal options across:
    - Logic types, Backends, Expression Nodes, Operators
  - Should be generally organised on a module by module basis for granular testing coverage and low level operations
  - Cover cross functional integrations
  - Be pararameterised wghere possible to allow a single test to cover all combinations. This is EXTREMELEY important for our scneario where every backend must produce the same results every time.
