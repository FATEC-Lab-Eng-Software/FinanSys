import test from "node:test";
import assert from "node:assert/strict";
import { routePathFromFileName, routesDirectory, generateRoutes } from "./generate-routes.mjs";

test("converte o nome de qualquer arquivo de rota em seu caminho URL", () => {
  assert.equal(routePathFromFileName("login.tsx"), "/login");
  assert.equal(routePathFromFileName("inserir-gasto.tsx"), "/inserir-gasto");
  assert.equal(routePathFromFileName("index.tsx"), "/");
  assert.match(routesDirectory, /src[\\/]routes$/);
});

test("inclui arquivos .tsx da pasta src/routes no manifesto", async () => {
  await generateRoutes();
  const { readFile } = await import("node:fs/promises");
  const manifest = await readFile(new URL("../src/generated/routes.ts", import.meta.url), "utf8");
  assert.match(manifest, /\.\.\/routes\/login"/);
  assert.ok(manifest.includes('"/login": route0.default'));
});
