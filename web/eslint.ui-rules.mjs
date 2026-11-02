// Design-system rules: off-system UI can't merge. See design/DESIGN.md.
// Generated tokens and scripts are outside the linted folders in eslint.config.mjs.
const BANNED_TEXT = [
  [/#[0-9a-fA-F]{3,8}\b/, "No raw hex colors: use a token (design/tokens/tokens.json)."],
  [/\b(rgb|hsl)a?\(/, "No rgb()/hsl() literals: use a token (design/tokens/tokens.json)."],
  [
    /\b[a-z][a-z-]*-\[[^\]]+\]/,
    "No arbitrary Tailwind values: use a token, or add one in tokens.json.",
  ],
  [/(^|[\s:])shadow(-[a-z0-9]+)?(?=\s|$)|box-shadow/, "No shadows: separate layers by tone."],
];

function checkText(context, node, text) {
  for (const [pattern, message] of BANNED_TEXT) {
    if (pattern.test(text)) context.report({ node, message });
  }
}

const noOffSystemValues = {
  meta: { type: "problem", schema: [] },
  create: (context) => ({
    Literal(node) {
      if (typeof node.value === "string") checkText(context, node, node.value);
    },
    TemplateElement(node) {
      checkText(context, node, node.value.raw);
    },
  }),
};

const noStyleOnComponents = {
  meta: { type: "problem", schema: [] },
  create: (context) => ({
    JSXAttribute(node) {
      const element = node.parent.name;
      const isComponent = element.type === "JSXIdentifier" && /^[A-Z]/.test(element.name);
      if (isComponent && node.name.name === "style") {
        context.report({ node, message: "No style prop on components: use variants or tokens." });
      }
    },
  }),
};

export const uiPlugin = {
  rules: {
    "no-off-system-values": noOffSystemValues,
    "no-style-on-components": noStyleOnComponents,
  },
};
