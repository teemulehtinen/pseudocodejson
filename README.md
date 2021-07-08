# pseudocodejson

JSON schema that can represent simple computer programs independent from any complete programming language. Tooling is designed to transform simple and restricted programs from e.g. Python and Java into a JSON data structure and vice versa.

#### Limitations

Implementations may severely limit the program language features that are supported. This issue is tolerable in a use-case such as introductory programming education.

#### Benefits

Targeting this programming language independent format allows to develop program analysis and simulations that do not depend on the original programming environment. This enables general solutions for code smell detection, code similarity checks, complexity analysis, program visualization, question generation, multi-language education, etc.

## TODO

* Implement Python to pseudocodejson
* Implement pseudocodejson to paddle
* Implement paddle to pseudocodejson
* Define JSON Schema https://json-schema.org/
