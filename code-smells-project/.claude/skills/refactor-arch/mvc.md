## MVC Implementation

MVC separates an application into three primary responsibilities:

* **Model** — represents application data, domain state, and domain-related behavior.
* **View** — represents data in a form suitable for the consumer.
* **Controller** — handles input, coordinates application flow, and selects the appropriate response.

The main objective of MVC is separation of concerns. Each component should have a clear responsibility and should not absorb responsibilities that belong to another component.

---

### Model

The Model represents the application's state and domain concepts.

It may contain:

* Domain entities
* Value objects
* Business invariants
* Domain validation
* State transitions
* Relationships between domain objects
* Persistence mappings when the framework couples persistence and domain models

The Model should:

* Represent meaningful business concepts
* Protect its own invariants when appropriate
* Keep domain-related rules close to the data they govern
* Remain independent from presentation concerns
* Avoid depending on HTTP concepts
* Expose meaningful operations instead of requiring external code to manipulate internal state directly
* Keep behavior related to the domain close to the corresponding domain object

The Model should not:

* Read HTTP requests
* Generate HTTP responses
* Return HTTP status codes
* Know about routes or endpoints
* Depend on Controllers
* Format data specifically for a user interface
* Contain unrelated orchestration logic
* Perform arbitrary infrastructure operations
* Become a container for unrelated application responsibilities

Examples of inappropriate responsibilities inside a Model include:

* Parsing request headers
* Returning JSON responses
* Redirecting users
* Managing route parameters
* Calling unrelated external services
* Coordinating entire application workflows

A Model should primarily describe **what the application represents and how its domain state behaves**.

---

### View

The View is responsible for presenting information to the consumer.

Depending on the application, a View may represent:

* HTML
* Templates
* JSON
* XML
* Serialized API responses
* UI models
* Response DTOs
* Other presentation formats

The View should:

* Receive already prepared data
* Represent that data in the required output format
* Handle presentation-specific formatting
* Keep presentation concerns isolated from domain logic
* Avoid introducing business decisions
* Remain replaceable without requiring changes to the domain model

The View may:

* Format dates
* Format numbers
* Rename fields for external representation
* Hide internal fields
* Transform internal models into public response structures
* Organize information for presentation purposes

The View should not:

* Execute business rules
* Access the database directly
* Perform authorization decisions
* Modify domain state
* Coordinate application workflows
* Perform complex validation
* Execute persistence operations
* Contain domain-specific decision logic

A useful rule is:

> The View may decide **how data is presented**, but it should not decide **what the business should do**.

In API-based applications, there may not be an explicit `views` directory. The View responsibility may instead be implemented through serializers, response models, DTOs, presenters, response mappers, or response-building logic.

The absence of a physical View class does not necessarily mean MVC is being violated.

---

### Controller

The Controller handles incoming input and coordinates the application flow.

It acts as the boundary between the external interface and the application.

The Controller should:

* Receive input from the external interface
* Extract route parameters
* Extract query parameters
* Extract headers when required
* Read request payloads
* Perform basic request-level validation
* Delegate business operations to the appropriate application or service component
* Handle expected application errors
* Select the appropriate response
* Define HTTP status codes in HTTP-based applications
* Pass prepared data to the View or response representation

The Controller should remain thin.

Its primary responsibility is orchestration, not implementation of business logic.

A Controller should generally follow this conceptual flow:

```text
Receive Input
      ↓
Validate Request Structure
      ↓
Delegate Operation
      ↓
Receive Result
      ↓
Produce Response
```

The Controller should not:

* Execute SQL directly
* Access database connections directly
* Implement substantial business rules
* Perform complex calculations related to the domain
* Contain large amounts of branching based on business state
* Reimplement domain validation
* Contain persistence logic
* Manage database transactions at a low level unless explicitly required by the framework or architecture
* Contain reusable business logic
* Coordinate infrastructure details directly when an application or service layer exists
* Become the central implementation point of the application

Common signs of an overloaded Controller include:

* Large methods
* Many nested conditionals
* Direct database queries
* Business calculations
* Multiple external integrations
* Persistence updates
* Domain decisions
* Repeated validation logic
* Data transformation unrelated to HTTP concerns

When these appear consistently, responsibilities should usually be extracted into appropriate components such as services, domain models, repositories, validators, or presenters.

---

### Responsibility Boundaries

A healthy MVC implementation should keep responsibilities approximately separated as follows:

```text
Controller
    ↓
Application / Domain Logic
    ↓
Model
```

For presentation:

```text
Controller
    ↓
View
    ↓
Consumer
```

When additional layers exist, a common structure is:

```text
Controller
    ↓
Service / Application Layer
    ↓
Model
    ↓
Repository / Persistence
```

The addition of Service or Repository layers does not invalidate MVC.

MVC defines separation between input coordination, domain/data representation, and presentation. Additional layers may be introduced to improve separation of concerns.

---

### Dependency Direction

Preferred dependencies:

```text
Controller → Application Logic
Controller → View
Application Logic → Model
View → Presentation Data
```

Acceptable variations may include:

```text
Controller → Service
Service → Model
Service → Repository
Repository → Model
```

Dependencies that should generally be avoided:

```text
Model → Controller
Model → HTTP Request
Model → HTTP Response

View → Database
View → Repository
View → Business Service for state-changing operations

Repository → Controller
Repository → View

Controller → Raw Database
Controller → SQL
```

The Model should remain as independent as reasonably possible from presentation and delivery mechanisms.

---

### Validation Responsibilities

Validation should be placed according to the type of rule being enforced.

#### Request validation

The Controller or request-validation component may validate:

* Required fields
* Input formats
* Invalid JSON or malformed payloads
* Unsupported query parameters
* Basic type constraints
* Request-specific constraints

#### Domain validation

The Model or domain layer should validate:

* Business invariants
* Valid state transitions
* Domain restrictions
* Rules that must remain true regardless of how the operation was invoked

For example, a rule that only exists because of HTTP belongs near the Controller.

A rule that must remain true whether the operation comes from HTTP, messaging, batch processing, or another source belongs in the domain or application layer.

---

### Error Handling

Controllers should translate application failures into presentation-level responses.

The domain should not need to know how errors are represented externally.

Preferred separation:

```text
Domain/Application Error
        ↓
Controller
        ↓
External Error Representation
```

The Controller may map:

* Not found conditions
* Validation failures
* Conflict conditions
* Authorization failures
* Unexpected failures

into the appropriate response format.

The Model should not contain HTTP-specific error handling.

---

### Data Transformation

Data transformation should respect architectural boundaries.

Inbound transformation:

```text
External Request
      ↓
Controller / Mapper
      ↓
Application or Domain Input
```

Outbound transformation:

```text
Domain / Application Result
      ↓
Presenter / Mapper / View
      ↓
External Response
```

Avoid passing transport-specific objects deeply into the Model.

Avoid exposing internal persistence models directly when doing so leaks implementation details or sensitive information.

---

### MVC Anti-Patterns

The following patterns may indicate poor MVC separation:

#### Fat Controller

A Controller contains:

* Business rules
* Persistence logic
* Complex calculations
* Large workflows
* Reusable application logic

#### Smart View

A View contains:

* Business rules
* Database access
* Domain decisions
* State-changing operations

#### Model Coupled to HTTP

A Model directly uses:

* Request objects
* Response objects
* HTTP status codes
* Route information
* Session-specific presentation concerns

#### Controller as Repository

Controllers execute:

* SQL
* ORM queries
* Database commands
* Persistence operations directly

#### Domain Logic Spread Across Controllers

The same business rule appears in multiple Controllers instead of a reusable domain or application component.

#### Presentation Leakage

Internal persistence or domain structures are exposed directly to external consumers without considering:

* Sensitive fields
* Stable API contracts
* Internal implementation details

---

### Architectural Evaluation Rules

When evaluating whether a project follows MVC:

* Do not rely exclusively on directory names.
* Do not assume a folder named `models` contains proper Models.
* Do not assume a folder named `controllers` contains thin Controllers.
* Inspect actual dependencies and responsibilities.
* Evaluate the direction of calls between components.
* Identify where business decisions are implemented.
* Identify where persistence occurs.
* Identify where external responses are constructed.
* Consider equivalent framework-specific abstractions.
* Do not require a literal `View` class for REST APIs.
* Do not classify the use of Service or Repository layers as a violation of MVC.
* Prefer responsibility-based analysis over naming conventions.

A project should be considered structurally aligned with MVC when input handling, domain/data responsibilities, and presentation concerns are meaningfully separated, even if additional architectural layers are present.
