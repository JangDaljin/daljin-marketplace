# 프로젝트 설정 파일

새 프로젝트를 만들 때 맞출 설정. 버전 번호는 설치 시점의 최신 안정판을 쓴다.

## package.json

```json
{
    "type": "module",
    "packageManager": "pnpm@<버전>",
    "engines": { "node": ">=<활성 LTS 메이저>" },
    "scripts": {
        "build": "nest build",
        "start:dev": "nest start --watch",
        "lint": "eslint .",
        "typecheck": "tsc --noEmit",
        "test": "vitest run --exclude \"test/**\"",
        "test:int": "vitest run test",
        "db:generate": "prisma generate",
        "db:validate": "prisma validate",
        "postinstall": "prisma generate",
        "prepare": "husky"
    }
}
```

- pnpm 10 이상은 의존성의 설치 스크립트를 막는다. `pnpm approve-builds` 로 `prisma`, `@prisma/engines`, `@swc/core` 등 필요한 것만 승인한다.
- 모노레포에서는 `postinstall` 대신 Turborepo 태스크 의존성으로 `db:generate` 를 먼저 돌린다.

## tsconfig.json

```json
{
    "compilerOptions": {
        "module": "NodeNext",
        "moduleResolution": "NodeNext",
        "target": "ES2023",
        "strict": true,
        "experimentalDecorators": true,
        "emitDecoratorMetadata": true,
        "skipLibCheck": true,
        "types": ["node"],
        "sourceMap": true,
        "outDir": "dist"
    },
    "include": ["src", "test"]
}
```

- TypeScript 6 부터 `types` 기본값이 빈 배열이라 `@types/node` 를 설치하고 `"types": ["node"]` 를 명시한다. 테스트에서 vitest 전역을 쓰지 않으므로 `vitest/globals` 는 넣지 않는다.
- `verbatimModuleSyntax` 는 켜지 않는다. 생성자 주입 타입의 import 가 바뀌어 DI 메타데이터가 깨질 수 있다.

## .swcrc

```json
{
    "$schema": "https://swc.rs/schema.json",
    "sourceMaps": true,
    "module": { "type": "es6" },
    "jsc": {
        "target": "es2022",
        "parser": { "syntax": "typescript", "decorators": true, "dynamicImport": true },
        "transform": { "legacyDecorator": true, "decoratorMetadata": true },
        "keepClassNames": true
    }
}
```

## nest-cli.json

```json
{
    "$schema": "https://json.schemastore.org/nest-cli",
    "collection": "@nestjs/schematics",
    "sourceRoot": "src",
    "compilerOptions": {
        "builder": "swc",
        "typeCheck": true,
        "deleteOutDir": true
    }
}
```

## vitest.config.ts

vitest 기본 변환기(esbuild)는 데코레이터 메타데이터를 만들지 않으므로 `unplugin-swc` 가 필수다.

```ts
import swc from "unplugin-swc";
import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        root: "./",
        include: ["src/**/*.spec.ts", "test/**/*.int-spec.ts"],
    },
    plugins: [swc.vite({ module: { type: "es6" } })],
});
```

## prisma/schema.prisma

ESM 으로 생성되는 `prisma-client` 제너레이터를 쓰고 출력 경로를 지정한다. 드라이버 어댑터, `prisma.config.ts` 필요 여부는 설치한 Prisma 버전 문서를 확인한다.

```prisma
generator client {
    provider     = "prisma-client"
    output       = "../src/generated/prisma"
    moduleFormat = "esm"
}
```

`.gitignore` 에 `src/generated/` 를 추가한다.

## 트랜잭션 (nestjs-cls)

`AppModule` 에 `ClsModule` 을 등록하고 `ClsPluginTransactional` 에 `TransactionalAdapterPrisma` 를 연결한다. `prismaInjectionToken` 은 `PrismaService` 로 둔다. 정확한 옵션은 설치한 `@nestjs-cls/transactional` 버전 문서를 확인한다.

## husky

```bash
pnpm add -D husky
pnpm exec husky init
```

`.husky/pre-push`:

```sh
pnpm db:validate
pnpm lint
pnpm typecheck
pnpm test
```

모노레포는 `pnpm turbo run db:validate lint typecheck test` 한 줄로 바꾼다. `husky init` 이 만든 `.husky/pre-commit` 은 지운다.

## 모노레포

`pnpm-workspace.yaml`:

```yaml
packages:
    - "apps/*"
    - "packages/*"
```

`turbo.json`:

```json
{
    "$schema": "https://turborepo.com/schema.json",
    "tasks": {
        "db:generate": { "cache": false },
        "db:validate": {},
        "build": { "dependsOn": ["^build", "db:generate"], "outputs": ["dist/**"] },
        "lint": { "dependsOn": ["^build"] },
        "typecheck": { "dependsOn": ["^build", "db:generate"] },
        "test": { "dependsOn": ["^build", "db:generate"] }
    }
}
```

- Nest 앱은 `apps/<이름>`, 공용 코드는 `packages/<이름>` 에 둔다.
- 각 패키지가 자기 `eslint.config.js`, `tsconfig.json`, `vitest.config.ts` 를 갖는다. 공통 설정은 `packages/config` 같은 패키지로 뽑아 가져다 쓴다.
