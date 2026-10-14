---
name: nestjs
description: NestJS + Prisma 기반 Node.js(TypeScript) 서버를 개인 규약대로 만들고 고치는 하네스. 프로젝트 셋업(pnpm, Turborepo, ESM, swc, husky), 코드 작성 규칙, ESLint 설정, vitest 테스트, push 전 검증 순서를 정한다. NestJS 서버를 새로 만들거나, 이 규약을 따르는 Node 서버 레포에서 기능을 추가하거나 고칠 때, "/developer:nestjs" 요청 시 사용.
---

# Node 서버 하네스

NestJS + Prisma 서버 작업을 시작 전 준비, 구현, 검증, 마무리 순서로 진행한다.

서버 공통 규칙(데이터베이스, Swagger, DTO, CORS)은 `developer:backend` 스킬에 있다. 이 하네스를 쓸 때 `backend` 스킬도 함께 불러 따른다. 이 문서는 그 규칙을 NestJS 로 구현하는 방법만 적는다.

이미 자체 규약(다른 린트 설정, CommonJS, npm 등)이 있는 레포에서는 레포 규약을 따른다. 이 하네스와 다른 점을 사용자에게 알리고, 사용자가 요청하기 전에는 레포 전체를 이 규약으로 바꾸지 않는다.

## 기술 스택

| 영역 | 선택 |
| --- | --- |
| 런타임, 언어 | Node.js 활성 LTS, TypeScript(`strict`), ESM |
| 프레임워크 | NestJS |
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

1. `pnpm dlx @nestjs/cli new <이름> --package-manager pnpm` 으로 만든다. 모노레포면 `apps/<이름>` 아래에 만든다.
2. `references/project-setup.md` 대로 설정 파일을 맞춘다: `package.json`, `tsconfig.json`, `.swcrc`, `nest-cli.json`, `vitest.config.ts`, Prisma `schema.prisma`, husky, (모노레포) `pnpm-workspace.yaml`, `turbo.json`.
3. `references/eslint.config.js` 를 프로젝트 루트에 복사하고 필요한 devDependency 를 설치한다.
4. `main.ts` 에서 Swagger(`SwaggerModule`)와 CORS(`app.enableCors`)를 설정한다. CORS 허용 출처는 `ConfigService` 로 읽는다. 무엇을 확인하고 정할지는 `backend` 스킬 4절을 따른다.
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
- Prisma 모델 객체를 Controller 에서 그대로 반환하지 않는다. Service 에서 Response DTO 로 바꿔 돌려준다(`backend` 스킬 3절).
- DTO 는 class 로 만든다. `ValidationPipe`(class-validator)와 Swagger 가 런타임에 class 정보를 읽기 때문이다.
- `any` 대신 `unknown` 을 쓰고 좁혀서 사용한다.
- DB 모델 타입은 Prisma 가 생성한 타입을 가져다 쓴다. 손으로 다시 정의하지 않는다.

### 2.3 함수와 흐름

- `var` 를 쓰지 않는다. 재할당이 없으면 `const` 를 쓴다.
- 비동기는 `async`/`await` 로 쓴다. `.then()` 체인을 쓰지 않는다. 에러는 `try`/`catch` 로 처리한다.
- `await` 하지 않는 Promise 를 남기지 않는다. 의도적으로 기다리지 않을 때는 `void` 를 붙이고 이유를 주석으로 남긴다.
- 짧은 콜백은 인라인으로 써도 된다: `users.filter((user) => user.active).map((user) => user.id)`
- 익명 함수를 그 자리에서 만들어 로직을 쌓지 않는다.
  - IIFE(`(() => { ... })()`, `(async () => { ... })()`)를 쓰지 않는다.
  - 콜백 본문에 블록(`{ ... }`)이 필요할 만큼 길어지면 이름 있는 `private` 메서드로 빼고 그 메서드를 넘긴다.
- 중첩 삼항 연산자를 쓰지 않는다. 문자열 연결은 템플릿 리터럴로 쓴다.
- `console` 대신 Nest `Logger` 를 쓴다.

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
- controller 는 HTTP 입출력만 맡는다. 비즈니스 로직은 service 에 둔다.
- service 는 `PrismaService` 를 직접 쓰지 않고 repository 를 주입받는다.
- 전역 `ValidationPipe` 를 `whitelist: true`, `forbidNonWhitelisted: true`, `transform: true` 로 켠다.
- 환경 변수는 `@nestjs/config` 로 읽는다. 코드에서 `process.env` 를 직접 읽지 않는다.

### 2.5 API 문서와 요청 검사

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

### 2.6 Prisma

- `PrismaService` 는 `PrismaClient` 를 상속하고 `OnModuleInit`, `OnModuleDestroy` 에서 연결과 해제를 한다. `@Global()` `PrismaModule` 에 한 번만 등록한다.
- DB 접근은 repository class 에만 둔다. repository 는 `TransactionHost<TransactionalAdapterPrisma>` 를 주입받아 `this.txHost.tx.<모델>` 로 쿼리한다. 그래야 트랜잭션 안팎에서 같은 코드가 동작한다.
- 트랜잭션은 service 메서드에 `@Transactional()` 을 붙여 건다. `prisma.$transaction` 을 직접 쓰지 않는다.
- 스키마를 바꾸면 `prisma migrate dev --name <설명>` 으로 마이그레이션을 만든다. 이미 적용된 마이그레이션 파일은 고치지 않는다. 배포 환경은 `prisma migrate deploy` 만 쓴다.
- 생성된 클라이언트(`src/generated/prisma`)는 커밋하지 않는다.
- `schema.prisma` 의 `datasource` provider 는 `backend` 스킬의 데이터베이스 규칙대로 `postgresql` 을 기본으로 쓴다.

## 3. 검증

push 전과 작업 완료 보고 전에 다음 순서로 모두 통과시킨다. 하나라도 실패하면 완료라고 하지 않는다.

1. `pnpm prisma validate`
2. `pnpm lint`
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

## 4. 마무리

- `git push --no-verify` 로 husky 를 건너뛰지 않는다.
- 사용자에게 다음을 보고한다.
  - 바꾼 파일과 이유
  - 검증 명령 4개의 결과. 실패나 건너뛴 단계가 있으면 그대로 적는다
  - 스키마를 바꿨다면 새 마이그레이션 이름
  - 이 하네스 규칙에서 벗어난 부분과 이유
