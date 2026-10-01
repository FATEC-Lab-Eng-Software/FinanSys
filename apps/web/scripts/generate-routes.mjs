import { mkdir, readdir, writeFile } from "node:fs/promises";
import { watch } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const webDirectory = path.resolve(scriptDirectory, "..");
export const routesDirectory = path.join(webDirectory, "src", "routes");
const generatedDirectory = path.join(webDirectory, "src", "generated");
const generatedFile = path.join(generatedDirectory, "routes.ts");

export function routePathFromFileName(fileName) {
  const name = fileName.replace(/\.tsx$/, "");
  return name === "index" ? "/" : `/${name}`;
}

function isRouteFile(fileName) {
  const name = fileName.slice(0, -4);
  return fileName.endsWith(".tsx") && !name.startsWith("_") && !name.includes(".");
}

export async function generateRoutes() {
  const entries = (await readdir(routesDirectory, { withFileTypes: true }).catch(() => []))
    .filter((entry) => entry.isFile() && isRouteFile(entry.name))
    .sort((left, right) => left.name.localeCompare(right.name));

  const imports = entries.map((entry, index) => `import * as route${index} from "../routes/${entry.name.slice(0, -4)}";`);
  const routes = entries.map((entry, index) => `  ${JSON.stringify(routePathFromFileName(entry.name))}: route${index}.default,`);

  await mkdir(generatedDirectory, { recursive: true });
  await writeFile(generatedFile, `${imports.join("\n")}\n\nexport const routes = {\n${routes.join("\n")}\n} as const;\n`, "utf8");
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  await mkdir(routesDirectory, { recursive: true });
  await generateRoutes();
  if (process.argv.includes("--watch")) {
    let timer;
    watch(routesDirectory, (_, fileName) => {
      if (!fileName?.endsWith(".tsx")) return;
      clearTimeout(timer);
      timer = setTimeout(() => generateRoutes(), 50);
    });
  }
}
