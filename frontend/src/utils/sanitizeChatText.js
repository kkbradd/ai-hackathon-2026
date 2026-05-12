/**
 * Removes model/tooling artifacts that should never appear in end-user chat.
 */
export function sanitizeChatText(text) {
  if (!text || typeof text !== "string") return text;
  let s = text;
  while (/<function[\s\S]*?<\/function>/i.test(s)) {
    s = s.replace(/<function[\s\S]*?<\/function>/gi, "");
  }
  s = s.replace(/<function[^>]+\/>/gi, "");
  s = s.replace(/<\/?function[^>]*>/gi, "");
  s = s.replace(/\n{3,}/g, "\n\n").trim();
  return s;
}
