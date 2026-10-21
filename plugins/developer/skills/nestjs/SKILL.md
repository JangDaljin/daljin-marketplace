---
name: nestjs
description: NestJS(Fastify) + Prisma 기반 Node.js(TypeScript) 서버를 개인 규약대로 만들고 고치는 하네스. 프로젝트 셋업(pnpm, Turborepo, ESM, swc, husky), @nestjs/config 프로필, pino 로깅, Helmet, 헬스 체크, axios 외부 호출, 코드 작성 규칙, ESLint 설정, vitest 테스트, push 전 검증 순서를 정한다. NestJS 서버를 새로 만들거나, 이 규약을 따르는 Node 서버 레포에서 기능을 추가하거나 고칠 때, "/developer:nestjs" 요청 시 사용.
---

# NestJS 하네스

NestJS(Fastify) + Prisma 서버 작업을 시작 전 준비, 구현, 검증, 마무리 순서로 진행한다.

서버 공통 규칙(작업 흐름, 데이터베이스, Swagger, DTO, 에러 응답, 날짜 형식, CORS)은 `developer:backend` 스킬에 있다. 이 하네스를 쓸 때 `backend` 스킬도 함께 불러 따른다. 특히 작업 흐름(설계 보고와 승인, 테스트 필수, 커밋 전 서브에이전트 코드 리뷰, 리팩터링 별도 커밋)은 `backend` 스킬 1절을 따른다. 이 문서는 그 규칙을 NestJS 로 구현하는 방법만 적는다.

작업 중인 프로젝트에 정의된 규칙(문서, 린트와 빌드 설정, CommonJS나 npm 같은 기존 선택, 이미 자리 잡은 구조와 관례)이 있으면 그 규칙이 최우선이다. 이 하네스와 `backend` 스킬의 같은 항목은 무시한다(`backend` 스킬 0절). 다른 점은 사용자에게 알리고, 프로젝트를 이 하네스에 맞게 바꾸지 않는다.

## 기술 스택

| 영역 | 선택 |
| --- | --- |
| 런타임, 언어 | Node.js 활성 LTS, TypeScript 6.0(`strict`), ESM |
| 프레임워크 | NestJS + Fastify (`@nestjs/platform-fastify`). Express 는 쓰지 않는다 |
| 설정 | `@nestjs/config`, 프로필 `local`, `develop`, `production` (`APP_ENV`) |
| 로깅 | pino (`nestjs-pino`), `local`/`develop` 은 `pino-pretty`, `production` 은 JSON |
| 보안 | `@fastify/helmet`. 요청 수 제한은 하지 않는다 |
| 헬스 체크 | `@nestjs/terminus` |
| HTTP 클라이언트 | axios (`axios.create()` 로 만든 인스턴스를 클라이언트 class 로 감싼다). `@nestjs/axios` 는 쓰지 않는다 |
| 날짜 | `Date`. 타임존 계산이 필요할 때만 Day.js (`utc`, `timezone` 플러그인) |
| 데이터베이스 | PostgreSQL (두 번째 선택 MySQL) |
| ORM | Prisma (repository class로 감싼다) |
| 트랜잭션 | `@nestjs-cls/transactional` + `@nestjs-cls/transactional-adapter-prisma` (`@Transactional()` 데코레이터) |
| 패키지 매니저 | pnpm. npm, yarn 은 쓰지 않는다 |
| 모노레포 | Turborepo + pnpm workspace. Nest CLI monorepo 모드는 쓰지 않는다 |
| 빌드 | swc (Nest CLI `builder: "swc"`, `typeCheck: true`) |
| API 문서 | `@nestjs/swagger` |
| 요청 검사 | `class-validator` + `class-transformer` (`ValidationPipe`) |
| 테스트 | vitest + `unplugin-swc` |
| 린트, 포맷 | ESLint flat config + typescript-eslint + `@stylistic`. Prettier, Biome 은 쓰지 않는다 |
| Git 훅 | husky `pre-push` |

라이브러리 API 가 버전마다 달라지는 부분(Prisma 제너레이터와 설정 파일, nestjs-cls 설정 등)은 작성 전에 context7 MCP 로 설치된 버전의 문서를 확인한다.

## 1. 시작 전 준비

### 1.1 새 프로젝트

1. `pnpm dlx @nestjs/cli new <이름> --package-manager pnpm` 으로 만든다. 모노레포면 `apps/<이름>` 아래에 만든다. Express 어댑터를 `@nestjs/platform-fastify` 로 바꾼다.
2. `references/project-setup.md` 대로 설정 파일을 맞춘다: `package.json`, `tsconfig.json`, `.swcrc`, `nest-cli.json`, `vitest.config.ts`, Prisma `schema.prisma`, `tsconfig.build.json`, `main.ts`, 환경 변수 검사, 로거 설정, husky, (모노레포) `pnpm-workspace.yaml`, `turbo.json`.
3. `references/eslint.config.js` 를 프로젝트 루트에 복사하고 필요한 devDependency 를 설치한다.
4. `main.ts` 에서 Fastify 어댑터(request id, `trustProxy`), pino 로거, Helmet, 종료 훅, Swagger(`SwaggerModule`), CORS(`app.enableCors`)를 설정한다. CORS 허용 출처는 `ConfigService` 로 읽는다. 무엇을 확인하고 정할지는 `backend` 스킬 6절을 따른다.
5. Nest CLI 가 만든 CommonJS 흔적(`require`, `module.exports`, `__dirname`)과 기본 Jest 설정을 지운다.
6. `pnpm lint && pnpm typecheck && pnpm test` 가 통과하는 상태에서 기능 작업을 시작한다.

### 1.2 기존 프로젝트

다음을 확인하고, 빠진 것이 있으면 바로 추가하지 말고 사용자에게 추가할지 묻는다.

- `package.json` 의 `"type": "module"`, `packageManager` 가 pnpm 인지
- `pnpm-lock.yaml` 이 있는지
- ESLint flat config 와 husky `pre-push` 가 있는지
- 모노레포면 `turbo.json` 이 있는지

## 2. 구현

### 2.1 모듈, import, export

- import 는 파일 맨 위, export 는 파일 맨 아래에 한 번만 둔다. 코드 중간에서 export 하지 않는다.
- 선언과 export 를 분리한다. `export class`, `export const`, `export function`, `export type X =` 처럼 선언과 함께 export 하지 않는다.
- 파일 끝에서 한 문장으로 내보낸다. 타입은 `type` 키워드를 붙여 같은 문장에 넣는다: `export { UserService, type UserSummary };`
- default export 는 쓰지 않는다. 도구가 요구하는 설정 파일(`eslint.config.js`, `vitest.config.ts` 등)만 예외다.
- 기본적으로 class 를 export 한다.
  - 상수는 class 의 `static readonly` 로 둔다. 최상위 `const` 를 export 하지 않는다.
  - 공용 함수도 class 의 `static` 메서드로 묶는다.
- `import * as` 를 쓰지 않는다. 필요한 것만 이름으로 가져온다.
- 상대 경로 import 에는 `.js` 확장자를 붙인다(`NodeNext` 규칙).
- Node 내장 모듈은 `node:` 접두사로 가져온다: `import { readFile } from "node:fs/promises";`
- Nest 가 생성자에 주입하는 class 는 `import type` 으로 가져오지 않는다. 타입 import 는 컴파일 후 지워져 DI 메타데이터가 사라진다. 순수 타입만 `import type` 또는 `import { type X }` 로 가져온다.

### 2.2 타입

- type alias 와 interface 중 하나면 `type` 을 쓴다.
- Prisma 모델 객체를 Controller 에서 그대로 반환하지 않는다. Service 에서 Response DTO 로 바꿔 돌려준다(`backend` 스킬 4절).
- DTO 는 class 로 만든다. `ValidationPipe`(class-validator)와 Swagger 가 런타임에 class 정보를 읽기 때문이다.
- `any` 대신 `unknown` 을 쓰고 좁혀서 사용한다.
- 값이 어떤 타입을 만족하는지 확인할 때는 `satisfies` 를 적극적으로 쓴다. 타입 단언(`as`)은 검사를 건너뛰므로 피한다.
  - 객체 리터럴에 `as Type` 을 쓰지 않는다. ESLint(`consistent-type-assertions`)가 막는다.
  - 설정 객체, 상수 목록, 매핑 테이블은 `satisfies` 로 타입을 확인하면서 리터럴 타입을 유지한다: `{ local: 10, production: 100 } satisfies Record<AppEnv, number>`
  - `as const` 는 써도 된다. `as const satisfies Type` 처럼 함께 쓸 수 있다.
- TypeScript `enum` 을 쓰지 않는다. 문자열 리터럴 union 타입이나 class 의 `static readonly` 값으로 표현한다.
- DB 모델 타입은 Prisma 가 생성한 타입을 가져다 쓴다. 손으로 다시 정의하지 않는다.

### 2.3 함수와 흐름

- `var` 를 쓰지 않는다. 재할당이 없으면 `const` 를 쓴다.
- 비동기는 `async`/`await` 로 쓴다. `.then()` 체인을 쓰지 않는다. 에러는 `try`/`catch` 로 처리한다.
- `await` 하지 않는 Promise 를 남기지 않는다. 의도적으로 기다리지 않을 때는 `void` 를 붙이고 이유를 주석으로 남긴다.
- 서로 관계없는 `await` 는 `Promise.all` 로 묶어 함께 기다린다. 동시에 실행할 개수를 제한해야 하면 `p-limit` 을 쓴다.
- 짧은 콜백은 인라인으로 써도 된다: `users.filter((user) => user.active).map((user) => user.id)`
- 익명 함수를 그 자리에서 만들어 로직을 쌓지 않는다.
  - IIFE(`(() => { ... })()`, `(async () => { ... })()`)를 쓰지 않는다.
  - 콜백 본문에 블록(`{ ... }`)이 필요할 만큼 길어지면 이름 있는 `private` 메서드로 빼고 그 메서드를 넘긴다.
- 중첩 삼항 연산자를 쓰지 않는다. 문자열 연결은 템플릿 리터럴로 쓴다.
- `console` 대신 Nest `Logger` 를 쓴다(2.8).

```ts
import { Injectable } from "@nestjs/common";

import { type User } from "../generated/prisma/client.js";
import { UserRepository } from "./user.repository.js";

@Injectable()
class UserService {
    public static readonly MAX_PAGE_SIZE = 100;

    constructor(private readonly userRepository: UserRepository) {}

    public async findActiveIds(): Promise<number[]> {
        const users = await this.userRepository.findAll();
        return users.filter((user) => user.active).map((user) => user.id);
    }

    public async summarize(): Promise<string[]> {
        const users = await this.userRepository.findAll();
        return users.map((user) => this.toSummary(user));
    }

    private toSummary(user: User): string {
        const status = user.active ? "active" : "inactive";
        return `${user.name} (${status})`;
    }
}

export { UserService };
```

### 2.4 NestJS 구조

- 도메인마다 feature module 을 둔다: `users/users.module.ts`, `users.controller.ts`, `users.service.ts`, `users.repository.ts`, `dto/`.
- 폴더는 Nest 방식대로 도메인별 module 로 나눈다. Java 하네스처럼 계층별 폴더(`controllers/`, `services/`)로 나누지 않는다. Nest 는 module 단위로 의존성 주입 범위를 묶기 때문이다.
- controller 는 HTTP 입출력만 맡는다. 비즈니스 로직은 service 에 둔다.
- service 는 `PrismaService` 를 직접 쓰지 않고 repository 를 주입받는다.
- 전역 `ValidationPipe` 를 `whitelist: true`, `forbidNonWhitelisted: true`, `transform: true` 로 켠다.

### 2.5 설정과 프로필

- 설정은 `@nestjs/config` 로 읽는다. 코드에서 `process.env` 를 직접 읽지 않는다. `main.ts` 와 `ConfigModule.forRoot` 의 `envFilePath` 만 예외다.
- 프로필은 `APP_ENV` 로 고른다: `local`, `develop`, `production`. 없으면 `local` 이다. `.env.<프로필>` 과 `.env` 순서로 읽는다.
- 환경 변수는 `Environment` class(class-validator)로 시작할 때 검사한다. 값이 없거나 틀리면 서버가 뜨지 않고 바로 실패한다. 숫자 값에는 `@Type(() => Number)` 를 붙인다. `.env` 값은 모두 문자열이기 때문이다.
- `.env.*` 파일은 커밋하지 않는다. 필요한 키 목록은 `.env.example` 로 커밋한다. 비밀값은 배포 환경의 환경 변수로 넣는다.

### 2.6 API 문서와 요청 검사

- Controller class 에 `@ApiTags`, 엔드포인트마다 `@ApiOperation({ summary })` 와 응답 코드별 `@ApiResponse` 를 붙인다.
- DTO 필드마다 `@ApiProperty` 를 붙인다. 선택 필드는 `@ApiPropertyOptional` 을 쓴다.
- Request DTO 필드마다 class-validator 데코레이터로 형식을 검사한다: `@IsString`, `@IsInt`, `@Length`, `@Min`, `@Max`, `@IsEmail`, `@IsEnum`, `@IsOptional` 등. 중첩 객체는 `@ValidateNested` 와 `@Type` 을 함께 쓴다.

```ts
import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import { IsEmail, IsOptional, IsString, Length } from "class-validator";

class CreateUserRequest {
    @ApiProperty({ maxLength: 50 })
    @IsString()
    @Length(1, 50)
    public name!: string;

    @ApiProperty()
    @IsEmail()
    public email!: string;

    @ApiPropertyOptional({ description: "가입 경로 코드" })
    @IsOptional()
    @IsString()
    public referralCode?: string;
}

export { CreateUserRequest };
```

### 2.7 에러 응답

- `backend` 스킬 5절의 형식(`statusCode`, `message`, `details`, `stack`)을 전역 `ExceptionFilter`(`@Catch()`) 한 곳에서 만든다. `HttpException` 이 아닌 예외는 500 으로 바꾼다.
- `ValidationPipe` 의 `exceptionFactory` 로 검사 오류를 `{ field, reason }` 목록으로 바꿔 `details` 에 담는다.
- `stack` 은 `ConfigService` 의 설정값(예: `ERROR_INCLUDE_STACK`)이 켜졌을 때만 넣는다. 기본값은 꺼짐이고 `.env.local`, `.env.develop` 에서만 켠다. 꺼져 있으면 응답 객체에 `stack` 키를 만들지 않는다.
- Fastify 가 만드는 오류(깨진 JSON 의 400, 없는 경로의 404)도 전역 필터를 거친다. 영어 원문 메시지는 정한 한국어 문구로 바꿔 응답한다.

### 2.8 로깅

- 로그는 pino 로 남긴다. `nestjs-pino` 의 `LoggerModule` 을 등록하고 `app.useLogger(app.get(Logger))` 로 Nest 로그도 pino 로 보낸다. 설정은 `references/project-setup.md` 의 `LoggerConfig` 를 따른다.
- class 안에서는 Nest `Logger` 를 쓴다: `private readonly logger = new Logger(UserService.name);`
- `local`, `develop` 은 `pino-pretty` 로 한 줄씩 보기 좋게, `production` 은 수집 도구가 읽도록 JSON 으로 남긴다.
  - pretty 형식: `[2026-10-14T17:46:41.689+09:00] INFO: [<request id>] UserService - 메시지`. 시각은 서버의 현재 시간과 오프셋이다.
  - JSON 의 `time` 은 ISO 8601 UTC 다.
- 요청마다 request id 를 붙인다(`backend` 스킬 9.1절). `FastifyAdapter` 에 `requestIdHeader: false` 와 `genReqId` 를 주고, `genReqId` 에서 `RequestId.from(req.headers["x-request-id"])` 로 형식을 검사한다. 형식에 맞으면 헤더 값을, 아니면 UUID 를 쓴다. `requestIdHeader` 에 헤더 이름을 주면 Fastify 가 값을 검사 없이 그대로 쓰므로 쓰지 않는다.
- 요청 완료 로그는 `GET /users 200 5ms` 형식으로 남긴다.
- `authorization`, `cookie`, `set-cookie` 헤더는 `redact` 로 가린다. 비밀번호, 토큰, 개인정보를 메시지에 넣지 않는다.
- 예외는 메시지와 스택을 함께 남긴다: ``this.logger.error(`결제 실패 orderId=${orderId}`, error instanceof Error ? error.stack : undefined)``
- 같은 예외를 잡을 때마다 로그를 남기고 다시 던지지 않는다. 처리하는 곳 한 번만 남긴다.

| 레벨 | 쓰는 경우 |
| --- | --- |
| `error` | 사람이 조치해야 하는 실패 |
| `warn` | 예상한 범위의 이상. 재시도로 회복, 잘못된 외부 응답 |
| `log`(info) | 주요 비즈니스 이벤트와 상태 변화 |
| `debug` | 개발 중 진단. `local`, `develop` 에서만 출력된다 |

### 2.9 날짜와 시간

- 날짜 응답 형식은 `backend` 스킬 4절대로 ISO 8601 UTC 문자열이다. Response DTO 의 날짜 필드는 `Date` 로 두면 JSON 직렬화 때 `toISOString()` 형식(`2026-10-14T08:00:00.000Z`)이 된다.
- Day.js 로 만든 문자열(`dayjs().format()`)을 응답에 그대로 넣지 않는다. 오프셋이 붙은 다른 형식이 나간다. 응답에는 `Date` 나 `toISOString()` 값만 넣는다.
- 요청의 날짜 필드는 문자열로 받아 `@IsISO8601({ strict: true })` 로 검사하고, service 에서 `new Date(value)` 로 바꾼다.
- 타임존 기준 계산(한국 시간 기준 하루, 월초 정산, 한국 시간 표시)이 필요할 때만 Day.js 를 쓴다. 플러그인 확장(`utc`, `timezone`)은 한 파일에서 한 번만 하고, 다른 파일은 그 파일에서 가져온다. 플러그인은 `dayjs/plugin/utc.js` 처럼 `.js` 를 붙여 가져온다.

### 2.10 보안

- `@fastify/helmet` 을 `main.ts` 에서 등록한다: `await app.register(helmet);`
- Swagger UI 가 Helmet 의 CSP 에 막히면 Swagger 경로에 맞게 `contentSecurityPolicy` 지시문을 조정한다. CSP 를 통째로 끄지 않는다.
- 요청 수 제한(`@nestjs/throttler`)은 쓰지 않는다(`backend` 스킬 9.3절).
- 로드밸런서나 프록시 뒤에서는 `FastifyAdapter` 의 `trustProxy` 에 앞단 프록시 수(`TRUST_PROXY_HOPS`)만큼만 믿는 함수를 준다: `trustProxy: (_address, hop) => hop < proxyHops`. 그래야 `req.ip` 가 실제 클라이언트 IP 가 된다. 프록시가 없는데 `true` 로 켜면 클라이언트가 `X-Forwarded-For` 로 IP 를 위조할 수 있다. Nest 의 `FastifyAdapter` 타입은 숫자를 받지 않으므로 함수로 준다.

### 2.11 외부 API 호출

공통 규칙은 `backend` 스킬 8절을 따른다.

- axios 를 쓴다. `@nestjs/axios`(HttpModule)는 쓰지 않는다. 결과가 RxJS Observable 이라 async/await 규칙과 맞지 않는다.
- 외부 서비스마다 클라이언트 class(`PaymentClient`)를 하나 만들고, 생성자에서 `axios.create()` 로 인스턴스를 만든다. 전역 `axios.get()` 을 직접 부르지 않는다.
- 클라이언트 class 는 `src/clients/<서비스>/` 에 두고 그 서비스의 module 로 묶는다.
- `baseURL` 과 `timeout` 은 설정값(`ConfigService`)에서 읽는다. `timeout` 은 반드시 정한다. axios 기본값은 무제한이다.
- request id 나 내부 식별자를 외부 호출 헤더로 넘기지 않는다(`backend` 스킬 8절). 인터셉터는 외부 API 가 요구하는 인증 헤더를 붙일 때만 쓴다.
- 응답 타입을 제네릭으로 정한다: `this.http.get<PaymentResponse>(path)`. 외부 응답 타입은 `type` 으로 정의한다.
- 오류는 클라이언트 class 안에서 `isAxiosError` 로 판별해 Nest 예외로 바꿔 던진다. 시간 초과(`ECONNABORTED`)는 `GatewayTimeoutException`(504), 그 밖의 외부 오류는 `BadGatewayException`(502)으로 바꾸고 `warn` 로그를 한 번 남긴다. axios 오류 객체를 그대로 밖으로 던지지 않는다. 요청 헤더와 설정이 담겨 있어 응답이나 로그로 새어 나갈 수 있다.
- 외부 API 는 트랜잭션(`@Transactional()`) 밖에서 부른다. 안에서 부르면 응답을 기다리는 동안 DB 커넥션을 붙잡는다.
- service 단위 테스트에서는 클라이언트 class 를 `vi.fn()` 가짜로 주입한다. 테스트에서 실제 외부 API 를 부르지 않는다.

### 2.12 이벤트 루프와 스레드 풀

- 요청 처리 중에 동기 API(`readFileSync`, `crypto.pbkdf2Sync` 등)를 쓰지 않는다. 이벤트 루프가 멈춰 모든 요청이 기다린다.
- CPU 를 오래 쓰는 작업(대용량 변환, 이미지 처리)은 worker thread 나 작업 큐로 넘긴다.
- libuv 스레드 풀 크기(`UV_THREADPOOL_SIZE`, 기본 4)를 실행 환경 변수로 16 으로 늘린다. 비밀번호 해시(bcrypt, argon2), 파일 I/O, 압축, `dns.lookup`(외부 API 호출 시 호스트 이름 조회)이 이 풀을 쓰기 때문에 4 개로는 요청이 몰릴 때 대기열이 생긴다. 네트워크 소켓(DB, HTTP)은 이 풀을 쓰지 않는다.
  - 코드의 `process.env` 로 바꾸지 않는다. 풀은 처음 쓰일 때 크기가 정해지므로 프로세스 시작 전에 정해야 한다. `package.json` 의 `start` 스크립트나 Dockerfile 의 `ENV` 로 넣는다.
  - 값은 부하 테스트로 조정한다. 너무 크게 잡으면 스레드마다 메모리를 쓰고 문맥 전환이 늘어난다.

### 2.13 운영

- 헬스 체크는 `@nestjs/terminus` 로 `GET /health` 를 만든다. DB 는 `PrismaHealthIndicator` 로 확인한다. 응답에 DB 주소나 설정을 넣지 않는다.
- `app.enableShutdownHooks()` 로 종료 신호를 받아 `PrismaService` 의 `onModuleDestroy` 에서 연결을 닫는다.
- Swagger 는 `APP_ENV` 가 `production` 이 아닐 때만 `SwaggerModule.setup` 을 부른다.
- 배포용 Dockerfile 과 GitHub Actions 예시는 `references/project-setup.md` 에 있다.

### 2.14 Prisma

- `PrismaService` 는 `PrismaClient` 를 상속하고 `OnModuleInit`, `OnModuleDestroy` 에서 연결과 해제를 한다. `@Global()` `PrismaModule` 에 한 번만 등록한다.
- DB 접근은 repository class 에만 둔다. repository 는 `TransactionHost<TransactionalAdapterPrisma>` 를 주입받아 `this.txHost.tx.<모델>` 로 쿼리한다. 그래야 트랜잭션 안팎에서 같은 코드가 동작한다.
- 트랜잭션은 service 메서드에 `@Transactional()` 을 붙여 건다. `prisma.$transaction` 을 직접 쓰지 않는다.
- 스키마를 바꾸면 `prisma migrate dev --name <설명>` 으로 마이그레이션을 만든다. 설명은 snake_case 로 동사와 대상을 쓴다: `--name create_orders`, `--name add_deleted_at_to_users`. Prisma 가 폴더 이름 앞에 시각을 붙인다(`20261014090000_create_orders`). 이미 적용된 마이그레이션 파일은 고치지 않는다. 배포 환경은 `prisma migrate deploy` 만 쓴다.
- 생성된 클라이언트(`src/generated/prisma`)는 커밋하지 않는다.
- 모델 필드는 camelCase(`createdAt`)로 쓰고 `@map("created_at")` 으로 snake_case 컬럼에 연결한다. 컬럼 이름 규칙은 `backend` 스킬 2.1절을 따른다.
- 기본 키, 인덱스, 유니크 키는 `map` 으로 이름을 정한다: `@id(map: "pk_orders")`, `@@index([userId], map: "idx_orders_user_id")`, `@@unique([email], map: "uk_users_email")`
- 관계 필드(`@relation`)와 관계 목록 필드를 절대 선언하지 않는다. 다른 테이블은 `userId Int` 같은 스칼라 필드로만 참조한다(`backend` 스킬 2.3절). 그래서 `include`, 중첩 `select`, 중첩 쓰기(`create: { ... }`)는 코드에 나타나지 않는다.
- 관계 필드가 없으면 Prisma 는 FK 를 만들지 않으므로, FK 제약은 마이그레이션 SQL 에 직접 넣는다. `prisma migrate dev --create-only` 로 SQL 을 만든 뒤 `ALTER TABLE orders ADD CONSTRAINT fk_orders_user_id FOREIGN KEY (user_id) REFERENCES users (id);` 를 추가하고 적용한다(DB 코멘트와 같은 방식). 이름은 `backend` 스킬 2.1절의 `fk_` 규칙, `ON DELETE` 는 기본 RESTRICT 다. `prisma migrate diff` 는 이 FK 를 스키마 드리프트로 보지 않는다. Prisma 가 모르는 제약이기 때문이다.
- 여러 테이블을 함께 읽어야 하면 repository 에서 나눠 조회한 뒤 id 로 묶는다. 한 번에 조인해야 하면 repository 안에서만 `$queryRaw` 로 쓴다.
- 감사 컬럼(`backend` 스킬 2.5절): `createdAt DateTime @default(now()) @db.Timestamptz @map("created_at")`, `updatedAt DateTime @updatedAt @db.Timestamptz @map("updated_at")`. `@updatedAt` 은 DB 가 아니라 Prisma Client 가 채운다. `createdBy`, `updatedBy` 는 repository 공통 처리에서 로그인 사용자 id 로 채운다.
- 시각 필드는 `DateTime @db.Timestamptz` 로 선언한다(PostgreSQL). Prisma 는 `DateTime` 을 UTC 로 읽고 쓴다(`backend` 스킬 2.4절).
- Prisma 스키마는 DB 코멘트를 만들지 않는다. DB 코멘트(`backend` 스킬 2.2절)는 `prisma migrate dev --create-only` 로 마이그레이션 SQL 을 만든 뒤 PostgreSQL 은 `COMMENT ON TABLE`, `COMMENT ON COLUMN` 을, MySQL 은 `COMMENT` 절을 직접 추가하고 적용한다. `schema.prisma` 에도 같은 내용을 `///` 주석으로 남긴다.
- `schema.prisma` 의 `datasource` provider 는 `backend` 스킬의 데이터베이스 규칙대로 `postgresql` 을 기본으로 쓴다.

## 3. 검증

push 전과 작업 완료 보고 전에 다음 순서로 모두 통과시킨다. 하나라도 실패하면 완료라고 하지 않는다.

1. `pnpm prisma validate`
2. `pnpm lint` (ESLint 가 계층 규칙도 검사한다. controller 가 repository, PrismaService, Prisma 모델을 가져오거나 service 가 PrismaService 를 가져오면 실패한다)
3. `pnpm typecheck` (swc 는 타입 검사를 하지 않으므로 빼지 않는다)
4. `pnpm test`

모노레포는 `pnpm turbo run db:validate lint typecheck test` 로 한 번에 돌린다.

테스트는 단위와 통합으로 나눈다.

| 종류 | 위치, 이름 | 방식 |
| --- | --- | --- |
| 단위 | 소스 옆 `*.spec.ts` | `Test.createTestingModule` 로 대상만 띄우고 repository 는 `vi.fn()` 으로 만든 가짜를 `useValue` 로 주입한다. DB 를 쓰지 않는다 |
| 통합 | `test/**/*.int-spec.ts` | Testcontainers 로 운영과 같은 DB(PostgreSQL 또는 MySQL) 를 띄우고 `prisma migrate deploy` 후 repository 와 트랜잭션을 실제로 검증한다 |

- 단위 테스트는 `pnpm test`, 통합 테스트는 `pnpm test:int` 로 따로 돌린다. `pre-push` 에는 단위 테스트만 넣고, 통합 테스트는 CI 에서 돌린다.
- 새 기능과 버그 수정에는 테스트를 함께 쓴다. 버그 수정은 먼저 실패하는 테스트를 쓴다.

테스트 작성 규칙:

- `it` 이름은 무엇을 확인하는지 한국어 문장으로 쓴다: `it("탈퇴한 회원은 로그인할 수 없다", ...)`
- 본문은 `// given`, `// when`, `// then` 주석으로 나눈다.
- 테스트 데이터는 `test/fixtures/` 의 fixture class 한 곳에서 만든다.

## 4. 마무리

- 커밋 전에 `backend` 스킬 1.3절의 서브에이전트 코드 리뷰를 하고, 결과를 보고한 뒤 사용자가 고르라고 한 지적만 고친다.
- `git push --no-verify` 로 husky 를 건너뛰지 않는다.
- 사용자에게 다음을 보고한다.
  - 바꾼 파일과 이유
  - 검증 명령 4개의 결과. 실패나 건너뛴 단계가 있으면 그대로 적는다
  - 스키마를 바꿨다면 새 마이그레이션 이름
  - 이 하네스 규칙에서 벗어난 부분과 이유
