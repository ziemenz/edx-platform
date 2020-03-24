/**
 * Used to ellipsize a section of arbitrary HTML after a specified number of words.
 *
 * Note: this will modify the DOM structure of root in place.
 * To keep the original around, you may want to save the result of cloneNode(true) before calling this method.
 *
 * Returns how many words remain (or a negative number if the content got clamped)
 */
function clampHtmlByWords(root, wordsLeft)
{
  let remaining = wordsLeft;

  // First, cut short any text in our node, as necessary
  if (root.nodeName === '#text' && root.data) {
    const words = root.data.split(/\s+/).filter(Boolean); // split on words, ignoring any resulting empty strings
    if (remaining < 0) {
      root.data = '';
    } else if (remaining > words.length) {
      remaining -= words.length;
    } else {
      // OK, let's add an ellipses and cut some of root.data
      root.data = `${words.slice(0, remaining).join(' ')}…`;
      remaining = -1;
    }
  }

  // Now do the same for any child nodes
  const nodes = Array.from(root.childNodes);
  nodes.forEach((node) => {
    if (remaining < 0) {
      root.removeChild(node);
    } else {
      remaining = clampHtmlByWords(node, remaining);
    }
  });

  return remaining;
}

export {
  clampHtmlByWords,
}
