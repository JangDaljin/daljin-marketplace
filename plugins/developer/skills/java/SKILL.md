---
name: java
description: Java/Spring Boot 서버를 개인 규약대로 만들고 고치는 하네스. Gradle 멀티 모듈(api, core, infra), 3 Layer 구조, Google Java Style, Hibernate + JPA + QueryDSL(OpenFeign), Liquibase, Swagger, JUnit 5 테스트, push 전 검증 순서를 정한다. Spring Boot 서버를 새로 만들거나, 이 규약을 따르는 Java 서버 레포에서 기능을 추가하거나 고칠 때, "/developer:java" 요청 시 사용.
---

# Java 하네스

Java/Spring Boot 서버 작업을 시작 전 준비, 구현, 검증, 마무리 순서로 진행한다.

서버 공통 규칙(데이터베이스, Swagger, DTO, CORS)은 `developer:backend` 스킬에 있다. 이 하네스를 쓸 때 `backend` 스킬도 함께 불러 따른다. 이 문서는 그 규칙을 Java/Spring 으로 구현하는 방법만 적는다.

이미 자체 규약이 있는 레포에서는 레포 규약을 따른다. 이 하네스와 다른 점을 사용자에게 알리고, 사용자가 요청하기 전에는 레포 전체를 이 규약으로 바꾸지 않는다.

## 기술 스택

| 영역 | 선택 |
| --- | --- |
| 언어 | Java 25 (LTS) |
| 프레임워크 | Spring Boot |
| 빌드 | Gradle (Kotlin DSL), 멀티 모듈 |
| 서버 구조 | 3 Layer (신규 서버는 Port-Adapter 검토) |
| 데이터베이스 | PostgreSQL (두 번째 선택 MySQL) |
| ORM | Hibernate + JPA + QueryDSL (OpenFeign 포크 `io.github.openfeign.querydsl`) |
| DB 마이그레이션 | Liquibase |
| 린트, 포맷 | Google Java Style (Checkstyle `google_checks.xml`, Spotless + google-java-format) |
| API 문서 | springdoc-openapi (Swagger) |
| 요청 검사 | Bean Validation (`jakarta.validation`) |
| 보일러플레이트 | Lombok (Entity, Service). DTO 는 `record` |
| 테스트 | JUnit 5 + AssertJ + Mockito, 통합 테스트는 Testcontainers |
| Git 훅 | `.githooks/pre-push` 에서 `./gradlew check` |

라이브러리 API 와 좌표가 버전마다 달라지는 부분(Spring Boot, springdoc, QueryDSL OpenFeign 의 annotation processor 좌표 등)은 작성 전에 context7 MCP 로 설치할 버전의 문서를 확인한다.

## 1. 시작 전 준비

### 1.1 서버 구조 결정

- 기본은 3 Layer(Controller, Service, Repository)다.
- 신규 서버를 구성할 때는 Port-Adapter(헥사고날) 구조가 더 적합한지 판단한다. 외부 연동이 많거나 도메인 규칙이 복잡해 인프라와 분리할 가치가 크면 Port-Adapter 를 검토한다.
- Port-Adapter 가 더 적합하다고 보면 코드를 쓰기 전에 사용자에게 설계안을 보여 주고 확인을 받는다. 설계안에는 모듈과 패키지 구조, 3 Layer 대신 고른 이유를 넣는다. 확인 전에는 구현을 시작하지 않는다.
- 기존 서버는 이미 쓰는 구조를 유지한다.

### 1.2 멀티 모듈

계층별로 모듈을 나눈다. 모든 모듈은 같은 최상위 패키지(예: `com.example.app`)를 쓴다.

| 모듈 | 담는 것 | 의존 |
| --- | --- | --- |
| `api` | Spring Boot 진입점, Controller, Request/Response DTO, 설정(CORS, Swagger), 예외 처리 | `core`, `infra`(runtimeOnly) |
| `core` | Service, Entity, Repository 인터페이스(Spring Data JPA, `XxxRepositoryCustom`) | 없음 |
| `infra` | QueryDSL 구현(`XxxRepositoryImpl`), Liquibase changelog, 외부 연동 클라이언트 | `core` |

- `api` 는 `infra` 의 class 를 코드에서 직접 참조하지 않는다.
- QueryDSL Q 클래스는 Entity 가 있는 `core` 에서 annotation processor 로 생성한다.
- 공통 빌드 설정(Java toolchain, Checkstyle, Spotless, 테스트 태스크)은 `buildSrc` 의 convention plugin 에 두고, 버전은 `gradle/libs.versions.toml` 에서 관리한다.

설정 파일 예시는 `references/project-setup.md` 에 있다.

### 1.3 린트 설정

- Checkstyle 에 Google 설정(`config/checkstyle/google_checks.xml`)을 적용하고 `maxWarnings = 0` 으로 둔다. Google 설정은 위반을 경고로만 내므로 이 값이 없으면 빌드가 실패하지 않는다.
- 포맷은 Spotless 의 `googleJavaFormat()` 으로 맞춘다. `./gradlew spotlessApply` 로 고친다.

### 1.4 CORS

- 새 서버는 처음 구성할 때 CORS 를 설정한다. 무엇을 확인하고 정할지는 `backend` 스킬 4절을 따른다.
- Spring Security 를 쓰면 `CorsConfigurationSource` 빈으로, 쓰지 않으면 `WebMvcConfigurer#addCorsMappings` 로 설정한다. 허용 출처는 `application.yml` 의 환경별 값에서 읽는다.

### 1.5 Git 훅

- `.githooks/pre-push` 에 `./gradlew check` 를 넣고 실행 권한을 준다.
- 프로젝트를 받은 뒤 한 번 `git config core.hooksPath .githooks` 를 실행한다.

### 1.6 기존 프로젝트

다음을 확인하고, 빠진 것이 있으면 바로 추가하지 말고 사용자에게 추가할지 묻는다.

- Gradle 멀티 모듈 구성과 모듈 의존 방향
- Checkstyle, Spotless 설정
- Liquibase changelog
- `.githooks/pre-push`

## 2. 구현

### 2.1 코드 스타일

- Google Java Style 을 따른다(들여쓰기 2칸, 한 줄 100자, 와일드카드 import 금지).
- `var` 사용을 피하고 타입을 명시한다.
- 람다는 메서드 참조로 쓸 수 있으면 메서드 참조를 쓴다: `users.stream().map(User::getId)`
- 메서드 참조로 쓸 수 없고 파라미터가 1개면 이름을 `it` 으로 쓴다: `users.stream().map(it -> it.getName().trim())`

### 2.2 계층

- Controller 는 HTTP 요청과 응답만 맡는다. 비즈니스 로직은 Service 에 둔다.
- DB 접근은 Repository 에만 둔다.
- Controller 가 Repository 를 직접 호출하지 않는다. 항상 Service 를 거친다.
- `@Transactional` 은 Service 에만 붙인다. 조회만 하는 메서드는 `@Transactional(readOnly = true)` 를 쓴다.

### 2.3 Entity 와 DTO

- Entity 를 API 응답으로 절대 그대로 내보내지 않는다. 요청도 Entity 로 바로 받지 않는다.
- Entity 에서 Response DTO 로 바꾸는 일은 Service 의 트랜잭션 안에서 끝낸다. Controller 는 DTO 만 다룬다.
- `spring.jpa.open-in-view` 는 `false` 로 둔다. 트랜잭션 밖에서 지연 로딩이 일어나지 않게 하기 위해서다.
- Request/Response DTO 는 `record` 로 만든다. 변환은 DTO 의 정적 팩터리로 쓴다: `UserResponse.from(user)`
- Entity 에는 `@Getter`, `@NoArgsConstructor(access = AccessLevel.PROTECTED)` 를 쓴다. `@Setter`, `@Data` 는 쓰지 않는다. 상태 변경은 의미 있는 이름의 메서드로 한다.
- Service 는 `@RequiredArgsConstructor` 로 생성자 주입을 받는다. 필드 주입(`@Autowired` 필드)은 쓰지 않는다.

### 2.4 데이터 접근

- Hibernate + JPA + QueryDSL(OpenFeign 포크)을 쓴다.
- 단순 CRUD 는 Spring Data JPA Repository 메서드로 쓴다.
- 조건이 바뀌는 동적 쿼리와 복잡한 조회는 QueryDSL 로 쓴다. `core` 에 `XxxRepositoryCustom` 인터페이스를, `infra` 에 같은 패키지로 `XxxRepositoryImpl` 구현을 두고 구현에서 `JPAQueryFactory` 를 쓴다.

### 2.5 DB 마이그레이션

- 스키마 변경은 Liquibase changelog 로만 한다. changelog 는 `infra/src/main/resources/db/changelog/` 에 둔다.
- 변경 하나에 changeSet 하나를 만든다. 이미 적용된 changeSet 은 고치지 않고 새 changeSet 을 추가한다.
- `spring.jpa.hibernate.ddl-auto` 는 `validate` 로 둔다. Hibernate 가 스키마를 만들거나 바꾸지 않게 한다.

### 2.6 API 문서

`backend` 스킬 2절의 규칙대로 작성하고, springdoc 애노테이션을 다음처럼 쓴다.

- Controller class 에 `@Tag` 를 붙인다.
- 엔드포인트마다 `@Operation(summary = ...)` 을 붙인다.
- 성공과 실패 응답 코드를 `@ApiResponse` 로 적는다.
- 요청, 응답 DTO 와 필드에 `@Schema` 를 붙인다. `description` 은 이름만으로 알 수 없는 정보가 있을 때만 적는다.

### 2.7 요청 검사

- Controller 의 요청 파라미터에 `@Valid` 를 붙인다: `create(@Valid @RequestBody CreateUserRequest request)`
- Request DTO 필드마다 Bean Validation 애노테이션을 건다: `@NotNull`, `@NotBlank`, `@Size`, `@Min`, `@Max`, `@Email`, `@Pattern` 등. 중첩 객체 필드에도 `@Valid` 를 붙인다.
- 검사 실패(`MethodArgumentNotValidException`)는 `@RestControllerAdvice` 에서 400 과 필드별 오류로 응답한다.
- Jackson 의 필드 이름 전략을 snake_case 로 바꾸지 않는다. 기본 camelCase 를 쓴다.

```java
@Schema(description = "회원 가입 요청")
public record CreateUserRequest(
    @Schema(maxLength = 50) @NotBlank @Size(max = 50) String name,
    @NotBlank @Email String email,
    @Schema(description = "가입 경로 코드") @Size(max = 20) String referralCode) {}
```

## 3. 검증

push 전과 작업 완료 보고 전에 다음을 모두 통과시킨다. 하나라도 실패하면 완료라고 하지 않는다.

1. `./gradlew check` (Spotless 검사, Checkstyle, 단위 테스트)
2. 스키마나 Repository 를 바꿨으면 `./gradlew integrationTest`
3. 새로 만든 엔드포인트가 Swagger UI 에 나오는지 확인한다

테스트는 단위와 통합으로 나눈다.

| 종류 | 대상, 방식 | 실행 |
| --- | --- | --- |
| 단위 | Service 는 Repository 를 Mockito 로 대체한다. Controller 는 `@WebMvcTest` 와 `@MockitoBean` 으로 Service 를 대체하고 요청 검사와 응답 형식을 확인한다. 검증은 AssertJ 로 쓴다 | `./gradlew test` (`pre-push` 에서 실행) |
| 통합 | `@Tag("integration")` 을 붙이고 Testcontainers 로 운영과 같은 DB 를 띄운다. Liquibase 를 적용한 뒤 Repository, QueryDSL 쿼리, 트랜잭션을 실제로 검증한다 | `./gradlew integrationTest` (CI 에서 실행) |

- 새 기능과 버그 수정에는 테스트를 함께 쓴다. 버그 수정은 먼저 실패하는 테스트를 쓴다.

## 4. 마무리

- `git push --no-verify` 로 훅을 건너뛰지 않는다.
- 사용자에게 다음을 보고한다.
  - 바꾼 파일과 이유
  - 검증 결과. 실패나 건너뛴 단계가 있으면 그대로 적는다
  - 스키마를 바꿨다면 추가한 Liquibase changeSet
  - 이 하네스 규칙에서 벗어난 부분과 이유
