## Anti-pattern Examples and Refactoring Guide

The examples below use Java syntax only for illustration. The underlying principles apply regardless of language or framework.

### CRITICAL

#### Security Vulnerability

##### SQL Injection

Bad:

```java
String sql = "SELECT * FROM users WHERE email = '" + email + "'";
database.execute(sql);
```

Better:

```java
String sql = "SELECT * FROM users WHERE email = ?";
database.execute(sql, email);
```

General rule:

* Never concatenate untrusted input into SQL.
* Use parameterized queries, prepared statements, query builders, or safe ORM mechanisms.
* Treat all external input as untrusted.

---

##### Exposed Credentials

Bad:

```java
String apiKey = "sk-production-secret-key";
String databasePassword = "super-secret-password";
```

Better:

```java
String apiKey = configuration.get("API_KEY");
String databasePassword = configuration.get("DATABASE_PASSWORD");
```

General rule:

* Do not store credentials in source code.
* Read secrets from environment variables, secret managers, or secure runtime configuration.
* Do not commit secrets to version control.

---

##### Sensitive Data Exposure

Bad:

```java
return new UserResponse(
    user.getId(),
    user.getEmail(),
    user.getPassword()
);
```

Better:

```java
return new UserResponse(
    user.getId(),
    user.getEmail()
);
```

General rule:

* Expose only the data required by the consumer.
* Never expose passwords, tokens, private keys, internal credentials, or unnecessary sensitive fields.
* Prefer explicit response models over directly serializing internal entities.

---

#### God Class / God Object

Bad:

```java
class OrderManager {

    void createOrder() {
        // validate request
        // calculate price
        // query database
        // process payment
        // send email
        // update inventory
        // generate invoice
        // write audit log
    }
}
```

Better:

```java
class OrderService {

    private final PricingService pricingService;
    private final PaymentService paymentService;
    private final InventoryService inventoryService;
    private final OrderRepository orderRepository;

    void createOrder(OrderRequest request) {
        pricingService.calculate(request);
        paymentService.process(request);
        inventoryService.reserve(request);
        orderRepository.save(request);
    }
}
```

General rule:

* A component should have a focused responsibility.
* Split unrelated responsibilities into dedicated components.
* Avoid central classes that know about every part of the system.
* Prefer cohesion over arbitrary class size limits.

---

### HIGH

#### Controller with Direct Database Access

Bad:

```java
class ProductController {

    ProductResponse getProduct(long id) {
        String sql = "SELECT * FROM products WHERE id = ?";
        Product product = database.query(sql, id);

        return ProductResponse.from(product);
    }
}
```

Better:

```java
class ProductController {

    private final ProductService productService;

    ProductResponse getProduct(long id) {
        Product product = productService.getProduct(id);

        return ProductResponse.from(product);
    }
}
```

```java
class ProductService {

    private final ProductRepository productRepository;

    Product getProduct(long id) {
        return productRepository.findById(id);
    }
}
```

General rule:

* Controllers should coordinate requests, not implement persistence.
* Database access belongs behind a persistence abstraction such as a repository or data-access component.
* Controllers should remain focused on transport concerns.

---

#### Poor or Missing Layer Separation

Bad:

```java
class UserController {

    Response createUser(Request request) {
        User user = new User();

        user.name = request.get("name");

        database.insert(user);

        emailClient.sendWelcomeEmail(user);

        return Response.ok(user);
    }
}
```

Better:

```java
class UserController {

    private final UserService userService;

    Response createUser(CreateUserRequest request) {
        User user = userService.create(request);
        return Response.ok(UserResponse.from(user));
    }
}
```

```java
class UserService {

    private final UserRepository userRepository;
    private final NotificationService notificationService;

    User create(CreateUserRequest request) {
        User user = User.create(request.name());

        userRepository.save(user);
        notificationService.sendWelcome(user);

        return user;
    }
}
```

General rule:

* Separate transport, application logic, domain logic, persistence, and infrastructure concerns.
* Do not require a specific number of layers.
* Evaluate separation by responsibility, not by folder names.

---

### MEDIUM

#### N+1 Query

Bad:

```java
List<Order> orders = orderRepository.findAll();

for (Order order : orders) {
    Customer customer = customerRepository.findById(order.getCustomerId());
    order.setCustomer(customer);
}
```

This may execute:

```text
1 query to load orders
+
N queries to load customers
```

Better:

```java
List<Order> orders = orderRepository.findAllWithCustomers();
```

Or:

```java
Set<Long> customerIds = extractCustomerIds(orders);

Map<Long, Customer> customers =
    customerRepository.findAllByIds(customerIds);

attachCustomers(orders, customers);
```

General rule:

* Avoid issuing one database query per item in a collection.
* Prefer joins, eager fetching when appropriate, batching, or bulk queries.
* Confirm that the optimization does not create excessive data loading.

---

#### High Cyclomatic Complexity / Callback Hell

Bad:

```java
void process(Order order) {
    if (order != null) {
        if (order.isActive()) {
            if (order.hasItems()) {
                if (order.getCustomer() != null) {
                    if (order.getCustomer().isVerified()) {
                        execute(order);
                    }
                }
            }
        }
    }
}
```

Better:

```java
void process(Order order) {
    validateOrder(order);
    execute(order);
}

void validateOrder(Order order) {
    if (order == null) {
        throw new InvalidOrderException();
    }

    if (!order.isActive()) {
        throw new InactiveOrderException();
    }

    if (!order.hasItems()) {
        throw new EmptyOrderException();
    }

    validateCustomer(order.getCustomer());
}
```

General rule:

* Reduce unnecessary nesting.
* Split independent decisions into focused operations.
* Prefer early exits when they make flow clearer.
* Extract meaningful rules instead of merely moving conditionals into different methods.
* For asynchronous code, avoid deeply nested callback chains and prefer structured composition mechanisms available in the language.

---

#### Long Function

Bad:

```java
void checkout(Order order) {
    // validate order
    // validate customer
    // calculate discounts
    // calculate taxes
    // calculate shipping
    // update inventory
    // process payment
    // persist order
    // generate invoice
    // send notification
}
```

Better:

```java
void checkout(Order order) {
    validate(order);

    Pricing pricing = pricingService.calculate(order);

    inventoryService.reserve(order);
    paymentService.process(order, pricing);

    orderRepository.save(order);

    notificationService.confirm(order);
}
```

General rule:

* Split functions when they contain multiple distinct responsibilities.
* Extract meaningful operations, not arbitrary blocks of lines.
* Function length alone is not sufficient evidence of a problem.
* Prefer high cohesion and clear intent.

---

### LOW

#### Magic Numbers

Bad:

```java
if (attempts > 3) {
    fail();
}

if (order.getTotal() > 1000) {
    requireApproval();
}
```

Better:

```java
private static final int MAX_RETRY_ATTEMPTS = 3;
private static final BigDecimal APPROVAL_THRESHOLD =
    new BigDecimal("1000");

if (attempts > MAX_RETRY_ATTEMPTS) {
    fail();
}

if (order.getTotal().compareTo(APPROVAL_THRESHOLD) > 0) {
    requireApproval();
}
```

General rule:

* Replace unexplained business-relevant literals with meaningful names.
* Do not create constants for universally obvious or purely structural values without benefit.

---

#### Poor Naming

Bad:

```java
void doIt(List<User> x) {
    for (User a : x) {
        send(a);
    }
}
```

Better:

```java
void sendNotifications(List<User> users) {
    for (User user : users) {
        sendNotification(user);
    }
}
```

General rule:

* Names should communicate intent and domain meaning.
* Avoid generic names such as `data`, `obj`, `tmp`, `manager`, or `helper` when a more specific concept exists.
* Short names are acceptable when their meaning is obvious from a very small scope.

---

#### Excessive Sequential Conditionals

Bad:

```java
if (price < 0) {
    throw new ValidationException("Invalid price");
}

if (stock < 0) {
    throw new ValidationException("Invalid stock");
}

if (name.length() < 2) {
    throw new ValidationException("Name too short");
}

if (name.length() > 200) {
    throw new ValidationException("Name too long");
}

if (!name.matches("[a-zA-Z ]+")) {
    throw new ValidationException("Invalid name");
}

if (category == null) {
    throw new ValidationException("Category required");
}
```

A few guard clauses are not inherently a problem.

The issue appears when validation grows enough to obscure the main responsibility of the function.

Better:

```java
void createProduct(CreateProductRequest request) {
    productValidator.validate(request);

    productService.create(request);
}
```

```java
class ProductValidator {

    void validate(CreateProductRequest request) {
        validatePrice(request.price());
        validateStock(request.stock());
        validateName(request.name());
        validateCategory(request.category());
    }
}
```

General rule:

* Do not flag a small number of clear guard clauses.
* Report this smell when conditionals materially reduce readability or mix validation with unrelated responsibilities.
* Group related validation rules when doing so improves cohesion.
* Do not introduce abstractions merely to eliminate `if` statements.
