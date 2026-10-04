import * as route0 from "../routes/cadastro";
import * as route1 from "../routes/esqueci-senha";
import * as route2 from "../routes/login";
import * as route3 from "../routes/password-recovery";

export const routes = {
  "/cadastro": route0.default,
  "/esqueci-senha": route1.default,
  "/login": route2.default,
  "/password-recovery": route3.default,
} as const;
