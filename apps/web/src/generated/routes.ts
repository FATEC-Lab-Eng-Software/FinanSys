import * as route0 from "../routes/esqueci-senha";
import * as route1 from "../routes/login";
import * as route2 from "../routes/password-recovery";

export const routes = {
  "/esqueci-senha": route0.default,
  "/login": route1.default,
  "/password-recovery": route2.default,
} as const;
