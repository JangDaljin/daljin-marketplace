---
name: java
description: Java/Spring Boot 서버를 개인 규약대로 만들고 고치는 하네스. Gradle 멀티 모듈(api, core, infra)과 계층별 패키지, 3 Layer 구조, Google Java Style, Hibernate + JPA + QueryDSL(OpenFeign, 연관관계 없이 id 참조), Liquibase, Swagger, Log4j2 + SLF4J 로깅, JSpecify, RestClient, 가상 스레드, JUnit 5 테스트, push 전 검증 순서를 정한다. Spring Boot 서버를 새로 만들거나, 이 규약을 따르는 Java 서버 레포에서 기능을 추가하거나 고칠 때, "/developer:java" 요청 시 사용.
---

# Java 하네스

Java/Spring Boot 서버 작업을 시작 전 준비, 구현, 검증, 마무리 순서로 진행한다.

서버 공통 규칙(작업 흐름, 데이터베이스, Swagger, DTO, 에러 응답, CORS, API 설계, 외부 API 호출, 운영)은 `developer:backend` 스킬에 있다. 이 하네스를 쓸 때 `backend` 스킬도 함께 불러 따른다. 특히 작업 흐름(설계 보고와 승인, 테스트 필수, 커밋 전 서브에이전트 코드 리뷰, 리팩터링 별도 커밋)은 `backend` 스킬 1절을 따른다. 이 문서는 그 규칙을 Java/Spring 으로 구현하는 방법만 적는다.

작업 중인 프로젝트에 정의된 규칙(문서, 빌드와 린트 설정, 이미 자리 잡은 구조와 관례)이 있으면 그 규칙이 최우선이다. 이 하네스와 `backend` 스킬의 같은 항목은 무시한다(`backend` 스킬 0절). 다른 점은 사용자에게 알리고, 프로젝트를 이 하네스에 맞게 바꾸지 않는다.

## 기술 스택

| 영역 | 선택 |
| --- | --- |
| 언어 | Java 25 (LTS) |
| 프레임워크 | Spring Boot |
| 빌드 | Gradle (Kotlin DSL), 멀티 모듈 |
| 서버 구조 | 3 Layer (신규 서버는 Port-Adapter 검토) |
| 데이터베이스 | PostgreSQL (두 번째 선택 MySQL) |
| ORM | Hibernate + JPA + QueryDSL (OpenFeign 포크 `io.github.openfeign.querydsl`). 연관관계 매핑은 쓰지 않는다 |
| DB 마이그레이션 | Liquibase |
| 린트, 포맷 | Google Java Style (Checkstyle `google_checks.xml`, Spotless + google-java-format) |
| API 문서 | springdoc-openapi (Swagger) |
| 요청 검사 | Bean Validation (`jakarta.validation`) |
| 로깅 | SLF4J(Lombok `@Slf4j`) + Log4j2 (`log4j2-spring.xml`) |
| 널 안전성 | JSpecify (`@NullMarked`, `@Nullable`) |
| HTTP 클라이언트 | `RestClient`. `RestTemplate` 은 쓰지 않는다 |
| 동시성 | 가상 스레드 (`spring.threads.virtual.enabled: true`) |
| 운영 | Spring Boot Actuator (헬스 체크), 보안 헤더 필터, request id 필터 |
| 구조 검사 | ArchUnit |
| 설정 | `@Value`, 프로필 `local`, `develop`, `production` |
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

### 1.2 멀티 모듈과 패키지

계층별로 모듈을 나누고, 모듈 안의 패키지도 계층별로 나눈다. 모든 모듈은 같은 최상위 패키지(예: `com.example.app`)를 쓴다.

| 모듈 | 패키지 | 담는 것 | 의존 |
| --- | --- | --- | --- |
| `api` | `controller`, `dto`, `config`, `exception` | Spring Boot 진입점, Controller, Request/Response DTO, 설정(CORS, Swagger, JPA Auditing, 필터), 전역 예외 처리 | `core`, `infra`(runtimeOnly) |
| `core` | `service`, `entity`, `repository`, `exception` | Service, Entity(`BaseEntity` 포함), Repository 인터페이스(Spring Data JPA, `XxxRepositoryCustom`), 비즈니스 예외 | 없음 |
| `infra` | `repository`, `client` | QueryDSL 구현(`XxxRepositoryImpl`), 외부 API 클라이언트, Liquibase changelog | `core` |

- 패키지는 도메인별(`user/`, `order/`)로 나누지 않고 계층별(`controller/`, `service/`)로 나눈다.
- `XxxRepositoryImpl` 은 `core` 의 Repository 인터페이스와 같은 `repository` 패키지에 둔다. Spring Data 가 이름과 패키지로 구현을 찾기 때문이다.
- `api` 는 `infra` 의 class 를 코드에서 직접 참조하지 않는다.
- QueryDSL Q 클래스는 Entity 가 있는 `core` 에서 annotation processor 로 생성한다.
- 계층 규칙은 ArchUnit 테스트(`api/src/test/java/.../architecture/LayerArchitectureTest`)로 빌드에서 막는다. Controller 가 Repository 나 Entity 에 의존하거나, `api` 가 `infra` 구현(`client`, `XxxRepositoryImpl`)에 의존하면 `./gradlew check` 가 실패한다.
- 공통 빌드 설정(Java toolchain, Checkstyle, Spotless, 테스트 태스크)은 `buildSrc` 의 convention plugin 에 두고, 버전은 `gradle/libs.versions.toml` 에서 관리한다.

설정 파일 예시는 `references/project-setup.md` 에 있다.

### 1.3 린트 설정

- Checkstyle 에 Google 설정(`config/checkstyle/google_checks.xml`)을 적용하고 `maxWarnings = 0` 으로 둔다. Google 설정은 위반을 경고로만 내므로 이 값이 없으면 빌드가 실패하지 않는다.
- 이 설정에서는 public class 와 public 메서드에 Javadoc 이 없으면 빌드가 실패한다(`MissingJavadocType`, `MissingJavadocMethod`). Javadoc 은 강제이므로 이 규칙을 끄지 않는다.
- `package-info.java` 의 Javadoc 도 의미 있는 문장으로 쓴다. `/** dto. */` 처럼 패키지 이름만 쓰면 `SummaryJavadoc` 규칙에 걸린다: `/** 요청과 응답 DTO. */`
- 포맷은 Spotless 의 `googleJavaFormat()` 으로 맞춘다. `./gradlew spotlessApply` 로 고친다.

### 1.4 프로필과 설정

- 프로필은 `local`, `develop`, `production` 세 가지다. `application.yml` 에 공통값을, `application-<프로필>.yml` 에 프로필별 값을 둔다. 기본 프로필은 `local` 이다.
- 설정값은 `@Value("${...}")` 로 주입받는다.
- `@Value` 는 `final` 필드에 붙이고 `@RequiredArgsConstructor` 로 주입한다. 이를 위해 루트 `lombok.config` 에 `lombok.copyableAnnotations += org.springframework.beans.factory.annotation.Value` 를 둔다.
- 비밀번호, 토큰 같은 비밀값은 yml 에 쓰지 않고 환경 변수로 받는다: `${DB_PASSWORD}`
- `application-production.yml` 에서 Swagger 를 끈다: `springdoc.api-docs.enabled: false`, `springdoc.swagger-ui.enabled: false`

### 1.5 CORS

- 새 서버는 처음 구성할 때 CORS 를 설정한다. 무엇을 확인하고 정할지는 `backend` 스킬 6절을 따른다.
- Spring Security 를 쓰면 `CorsConfigurationSource` 빈으로, 쓰지 않으면 `WebMvcConfigurer#addCorsMappings` 로 설정한다. 허용 출처는 프로필별 yml 값에서 읽는다.

### 1.6 Git 훅

- `.githooks/pre-push` 에 `./gradlew check` 를 넣고 실행 권한을 준다.
- 프로젝트를 받은 뒤 한 번 `git config core.hooksPath .githooks` 를 실행한다.

### 1.7 기존 프로젝트

다음을 확인하고, 빠진 것이 있으면 바로 추가하지 말고 사용자에게 추가할지 묻는다.

- Gradle 멀티 모듈 구성과 모듈 의존 방향
- Checkstyle, Spotless 설정
- Liquibase changelog
- Log4j2 설정, 프로필 구성
- `.githooks/pre-push`

## 2. 구현

### 2.1 코드 스타일

- Google Java Style 을 따른다(들여쓰기 2칸, 한 줄 100자, 와일드카드 import 금지).
- public class 와 public 메서드에는 Javadoc 을 반드시 단다. Checkstyle 이 빠진 Javadoc 을 빌드 실패로 막는다. 내용은 한 줄 요약으로 충분하다: `/** 활성 회원 이름 목록을 조회한다. */`
- `var` 사용을 피하고 타입을 명시한다.
- 람다는 메서드 참조로 쓸 수 있으면 메서드 참조를 쓴다: `users.stream().map(User::getId)`
- 메서드 참조로 쓸 수 없고 파라미터가 1개면 이름을 `it` 으로 쓴다: `users.stream().map(it -> it.getName().trim())`

### 2.2 계층

- Controller 는 HTTP 요청과 응답만 맡는다. 비즈니스 로직은 Service 에 둔다.
- DB 접근은 Repository 에만 둔다.
- Controller 가 Repository 를 직접 호출하지 않는다. 항상 Service 를 거친다.
- `@Transactional` 은 Service 에만 붙인다. 조회만 하는 메서드는 `@Transactional(readOnly = true)` 를 쓴다.
- 외부 API 호출은 트랜잭션 밖에서 한다. 트랜잭션 안에서 호출하면 응답을 기다리는 동안 DB 커넥션을 붙잡는다.

### 2.3 Entity 와 DTO

- Entity 를 API 응답으로 절대 그대로 내보내지 않는다. 요청도 Entity 로 바로 받지 않는다.
- Entity 에서 Response DTO 로 바꾸는 일은 Service 의 트랜잭션 안에서 끝낸다. Controller 는 DTO 만 다룬다.
- Entity 는 `BaseEntity` 를 상속한다. `BaseEntity` 는 `@CreatedDate`, `@LastModifiedDate`, `@CreatedBy`, `@LastModifiedBy` 로 감사 컬럼(`backend` 스킬 2.5절)을 채운다. JPA Auditing 은 `DateTimeProvider` 로 UTC `ZonedDateTime` 을, `AuditorAware<Long>` 로 로그인 사용자 id 를 공급한다. 인증이 아직 없으면 `AuditorAware` 는 빈 값을 돌려준다.
- `spring.jpa.open-in-view` 는 `false` 로 둔다. Controller 와 뷰에서 영속성 컨텍스트를 쓰지 않게 하기 위해서다.
- Request/Response DTO 는 `record` 로 만든다. 변환은 DTO 의 정적 팩터리로 쓴다: `UserResponse.from(user)`
- Entity 에는 `@Getter`, `@NoArgsConstructor(access = AccessLevel.PROTECTED)` 를 쓴다. `@Setter`, `@Data` 는 쓰지 않는다. 상태 변경은 의미 있는 이름의 메서드로 한다.
- Entity 에 연관관계 애노테이션(`@ManyToOne`, `@OneToMany`, `@OneToOne`, `@ManyToMany`, `@JoinColumn`, `@ElementCollection`)을 절대 쓰지 않는다. 다른 테이블은 id 필드(`private Long userId;`)로만 참조한다(`backend` 스킬 2.3절). 그래서 `FetchType`, `cascade`, `orphanRemoval`, `@EntityGraph`, `fetchJoin()` 은 코드에 나타나지 않는다.
- id 는 `@GeneratedValue(strategy = GenerationType.IDENTITY)` 로 두고, Liquibase 에서는 `bigint` `autoIncrement: true` 로 만든다. 전략을 생략하면 Hibernate 가 시퀀스를 찾아 changelog 와 맞지 않는다.
- enum 필드는 `@Enumerated(EnumType.STRING)` 으로 저장한다.
- 시각 필드는 `ZonedDateTime` 을 쓴다. `LocalDateTime` 은 타임존 정보가 없어 쓰지 않는다.
- DB 에는 UTC 로 저장되도록 `hibernate.timezone.default_storage: NORMALIZE_UTC` 와 `hibernate.jdbc.time_zone: UTC` 를 설정한다(`backend` 스킬 2.4절). DB 에서 읽은 값은 UTC 존이므로, 다른 타임존으로 보여 줘야 하면 `withZoneSameInstant(...)` 로 바꾼다.
- Service 는 `@RequiredArgsConstructor` 로 생성자 주입을 받는다. 필드 주입(`@Autowired` 필드)은 쓰지 않는다.

### 2.4 데이터 접근

- Hibernate + JPA + QueryDSL(OpenFeign 포크)을 쓴다.
- 단순 CRUD 는 Spring Data JPA Repository 메서드로 쓴다.
- 조건이 바뀌는 동적 쿼리와 복잡한 조회는 QueryDSL 로 쓴다. `core` 의 `repository` 에 `XxxRepositoryCustom` 인터페이스를, `infra` 의 같은 패키지에 `XxxRepositoryImpl` 구현을 두고 구현에서 `JPAQueryFactory` 를 쓴다.
- 연관관계가 없으므로 조인은 참조 컬럼으로 직접 건다. Hibernate 가 lazy/eager 로 몰래 쿼리를 더 날리는 일이 없고, 어떤 테이블을 읽는지 쿼리에 그대로 보인다.

```java
queryFactory
    .selectFrom(order)
    .join(user)
    .on(user.id.eq(order.userId))
    .where(user.active.isTrue())
    .fetch();
```

### 2.5 DB 마이그레이션

- 스키마 변경은 Liquibase changelog 로만 한다. changelog 는 `infra/src/main/resources/db/changelog/` 에 둔다.
- `db.changelog-master.yaml` 은 `includeAll` 로 `changes/` 폴더를 읽는다. 변경 파일은 `changes/<yyyyMMdd>-<순번 2자리>-<설명>.yaml` 로 만든다: `changes/20261014-01-create-orders.yaml`. 이름 순으로 적용되므로 날짜와 순번을 꼭 붙인다.
- 파일 하나에 changeSet 하나를 둔다. changeSet `id` 는 파일 이름(확장자 제외), `author` 는 git 사용자 이름으로 쓴다.
- 이미 적용된 changeSet 은 고치지 않고 새 파일을 추가한다.
- 기본 키, 인덱스, 유니크 키 이름은 `backend` 스킬 2.1절대로 Liquibase changeSet(`primaryKeyName`, `uniqueConstraintName`, `indexName`)에 적는다. Entity 에도 `@Index(name = "idx_...")`, `@UniqueConstraint(name = "uk_...")` 로 똑같이 적는다.
- `addForeignKeyConstraint` 는 기본으로 쓰지 않는다. 사용자가 FK 제약을 요청한 테이블에만 쓰고, `constraintName` 은 `backend` 스킬 2.1절의 `fk_` 규칙으로 적는다(`fk_orders_user_id`). `onDelete`, `onUpdate` 는 사용자가 지정할 때만 넣는다.
- DB 코멘트(`backend` 스킬 2.2절)는 Liquibase 의 `remarks` 로 단다. 새 테이블은 `createTable` 과 각 `column` 에 `remarks` 를 넣고, 기존 테이블은 `setTableRemarks`, `setColumnRemarks` 로 단다. 스키마의 기준은 Liquibase 이므로 Entity 의 `@Comment` 는 필수가 아니다.
- 시각 컬럼은 PostgreSQL 에서 `timestamptz` 로 만든다.
- Entity 필드는 camelCase(`createdAt`)로 쓴다. Spring Boot 기본 이름 전략이 snake_case 컬럼(`created_at`)으로 바꾼다.
- `spring.jpa.hibernate.ddl-auto` 는 `validate` 로 둔다. Hibernate 가 스키마를 만들거나 바꾸지 않게 한다.

### 2.6 API 문서

`backend` 스킬 3절의 규칙대로 작성하고, springdoc 애노테이션을 다음처럼 쓴다.

- Controller class 에 `@Tag` 를 붙인다.
- 엔드포인트마다 `@Operation(summary = ...)` 을 붙인다.
- 성공과 실패 응답 코드를 `@ApiResponse` 로 적는다.
- 요청, 응답 DTO 와 필드에 `@Schema` 를 붙인다. `description` 은 이름만으로 알 수 없는 정보가 있을 때만 적는다.

### 2.7 요청 검사

- Controller 의 요청 파라미터에 `@Valid` 를 붙인다: `create(@Valid @RequestBody CreateUserRequest request)`
- Request DTO 필드마다 Bean Validation 애노테이션을 건다: `@NotNull`, `@NotBlank`, `@Size`, `@Min`, `@Max`, `@Email`, `@Pattern` 등. 중첩 객체 필드에도 `@Valid` 를 붙인다.
- 검사 실패(`MethodArgumentNotValidException`)는 400 으로, 필드별 오류는 `details` 에 담는다.
- 본문을 읽지 못한 경우(`HttpMessageNotReadableException`: 깨진 JSON, 날짜 형식 오류)도 400 으로 응답한다.

```java
@Schema(description = "회원 가입 요청")
public record CreateUserRequest(
    @Schema(maxLength = 50) @NotBlank @Size(max = 50) String name,
    @NotBlank @Email String email,
    @Schema(description = "가입 경로 코드") @Size(max = 20) @Nullable String referralCode) {}
```

### 2.8 에러 응답

- `backend` 스킬 5절의 형식(`statusCode`, `message`, `details`, `stack`)을 `record ErrorResponse` 로 만들고, `@RestControllerAdvice`(`GlobalExceptionHandler`) 한 곳에서 모든 예외를 이 형식으로 바꾼다(`references/project-setup.md`).
- `stack` 은 `app.error.include-stack` 설정값이 `true` 일 때만 채운다. `application-local.yml`, `application-develop.yml` 에서 `true`, `application-production.yml` 과 공통 기본값은 `false` 다. 채우지 않을 때는 `null` 로 두고 `@JsonInclude(JsonInclude.Include.NON_NULL)` 로 키를 뺀다.
- Jackson 의 필드 이름 전략을 snake_case 로 바꾸지 않는다. 기본 camelCase 를 쓴다.
- 날짜 응답은 `backend` 스킬 4절대로 UTC ISO 8601 문자열이다. `spring.jackson.time-zone: UTC` 를 설정하면 `ZonedDateTime` 이 어느 존이든 `2026-10-14T08:00:00Z` 처럼 UTC 로 나간다. 이 설정이 없으면 `+09:00` 같은 원래 오프셋이 그대로 나간다.

### 2.9 로깅

- 로그는 Lombok `@Slf4j` 로 만든 SLF4J 로거로 남긴다. `System.out`, `printStackTrace()` 를 쓰지 않는다.
- 구현체는 Log4j2 다. `spring-boot-starter-logging` 을 빼고 `spring-boot-starter-log4j2` 를 쓰며, 설정은 `api/src/main/resources/log4j2-spring.xml` 에 둔다(`references/project-setup.md`).
- 로그 형식: `<현재 시각과 오프셋> <레벨> [<스레드>] [<request id>] <로거> - <메시지>`
- request id 는 `RequestIdFilter` 가 요청마다 MDC 의 `requestId` 에 넣는다(`backend` 스킬 9.1절). `x-request-id` 헤더가 형식에 맞으면 그 값을, 아니면 UUID 를 쓴다. Log4j2 형식에서 `%X{requestId}` 로 찍는다.
- 메시지는 문자열 연결 대신 자리표시자로 쓴다: `log.info("주문 생성 orderId={}", orderId)`
- 예외는 마지막 인자로 넘겨 스택 트레이스를 남긴다: `log.error("결제 실패 orderId={}", orderId, e)`
- 같은 예외를 잡을 때마다 로그를 남기고 다시 던지지 않는다. 처리하는 곳 한 번만 남긴다.
- 비밀번호, 토큰, 주민등록번호, 카드 번호 같은 민감정보는 로그에 남기지 않는다.

| 레벨 | 쓰는 경우 |
| --- | --- |
| `ERROR` | 사람이 조치해야 하는 실패 |
| `WARN` | 예상한 범위의 이상. 재시도로 회복, 잘못된 외부 응답 |
| `INFO` | 주요 비즈니스 이벤트와 상태 변화 |
| `DEBUG` | 개발 중 진단. `local`, `develop` 프로필에서만 출력된다 |

### 2.10 널 안전성

- 모든 패키지에 `package-info.java` 를 두고 `@NullMarked` 를 붙인다. 따로 표시하지 않은 타입은 null 이 아닌 것으로 본다.
- null 을 허용하는 필드, 파라미터, 반환값에만 `org.jspecify.annotations.Nullable` 을 붙인다.

```java
/** 회원 서비스. */
@NullMarked
package com.example.app.service;

import org.jspecify.annotations.NullMarked;
```

### 2.11 외부 API 호출

공통 규칙은 `backend` 스킬 8절을 따른다.

- `RestClient` 를 쓴다. `RestTemplate` 은 새 코드에 쓰지 않는다.
- 클라이언트 class 는 `infra` 의 `client` 패키지에 둔다. Spring 이 제공하는 `RestClient.Builder` 를 주입받아 base URL 과 기본 헤더를 정한다.
- 연결 타임아웃과 읽기 타임아웃을 반드시 설정한다. 값은 프로필별 yml 에 둔다.
- 외부 응답 DTO 도 `record` 로 만든다.
- 오류는 클라이언트 class 안에서 바꿔 던진다.
  - `ResourceAccessException` 의 원인이 `SocketTimeoutException` 이나 `java.net.http.HttpTimeoutException` 이면 시간 초과로 보고 504 예외로 바꾼다.
  - 그 밖의 `ResourceAccessException`, `RestClientResponseException` 은 502 예외로 바꾼다.
  - 외부 응답 본문과 헤더를 예외 메시지에 넣지 않는다. `warn` 로그에 상태 코드만 남긴다.

### 2.12 가상 스레드

- `spring.threads.virtual.enabled: true` 로 요청 처리와 `@Async`, 스케줄러를 가상 스레드에서 돌린다.
- 가상 스레드를 풀로 만들지 않는다. 동시에 실행할 수를 제한해야 하면 `Semaphore` 를 쓴다.
- 동시 요청이 늘어도 DB 동시성의 상한은 커넥션 풀(Hikari) 크기다. 풀 크기는 DB 가 감당할 수 있는 수로 정한다.
- 요청마다 무거운 객체를 `ThreadLocal` 에 캐시하지 않는다. 가상 스레드는 요청마다 새로 만들어져 캐시가 재사용되지 않는다.

### 2.13 운영

- 헬스 체크는 Actuator 를 쓴다. `management.endpoints.web.exposure.include: health` 로 `/actuator/health` 만 열고, `management.endpoint.health.show-details: never` 로 내부 정보를 숨긴다.
- 정상 종료: `server.shutdown: graceful`, `spring.lifecycle.timeout-per-shutdown-phase: 30s`
- 보안 헤더는 `SecurityHeadersFilter` 가 붙인다(`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Strict-Transport-Security`). Spring Security 를 쓰는 프로젝트는 필터 대신 Spring Security 의 기본 헤더 설정을 쓴다.
- 요청 수 제한은 구현하지 않는다(`backend` 스킬 9.3절).
- 배포용 Dockerfile 과 GitHub Actions 예시는 `references/project-setup.md` 에 있다.

## 3. 검증

push 전과 작업 완료 보고 전에 다음을 모두 통과시킨다. 하나라도 실패하면 완료라고 하지 않는다.

1. `./gradlew check` (Spotless 검사, Checkstyle, 단위 테스트, ArchUnit)
2. 스키마나 Repository 를 바꿨으면 `./gradlew integrationTest`
3. 새로 만든 엔드포인트가 Swagger UI 에 나오는지 확인한다

테스트는 단위와 통합으로 나눈다.

| 종류 | 대상, 방식 | 실행 |
| --- | --- | --- |
| 단위 | Service 는 Repository 를 Mockito 로 대체한다. Controller 는 `@WebMvcTest` 와 `@MockitoBean` 으로 Service 를 대체하고 요청 검사와 응답 형식을 확인한다 | `./gradlew test` (`pre-push` 에서 실행) |
| 통합 | `@Tag("integration")` 을 붙이고 Testcontainers 로 운영과 같은 DB 를 띄운다. Liquibase 를 적용한 뒤 Repository, QueryDSL 쿼리, 트랜잭션을 실제로 검증한다 | `./gradlew integrationTest` (CI 에서 실행) |

테스트 작성 규칙:

- 테스트 메서드에 `@DisplayName` 으로 무엇을 확인하는지 한국어 문장으로 적는다: `@DisplayName("탈퇴한 회원은 로그인할 수 없다")`
- 본문은 `// given`, `// when`, `// then` 주석으로 나눈다.
- 검증은 AssertJ(`assertThat`)로 쓴다.
- 테스트 데이터는 `XxxFixture` class 한 곳에서 만든다. 여러 모듈에서 쓰는 fixture 는 Gradle `java-test-fixtures` 플러그인으로 `src/testFixtures/java` 에 두고 공유한다.

## 4. 마무리

- 커밋 전에 `backend` 스킬 1.3절의 서브에이전트 코드 리뷰를 하고, 결과를 보고한 뒤 사용자가 고르라고 한 지적만 고친다.
- `git push --no-verify` 로 훅을 건너뛰지 않는다.
- 사용자에게 다음을 보고한다.
  - 바꾼 파일과 이유
  - 검증 결과. 실패나 건너뛴 단계가 있으면 그대로 적는다
  - 스키마를 바꿨다면 추가한 Liquibase changeSet
  - 이 하네스 규칙에서 벗어난 부분과 이유
