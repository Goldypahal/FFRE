import { useEffect, useRef } from "react";

/**
 * Prepares a `.ffl` root: switches on the scripted styles, enables smooth anchor
 * scrolling while the page is mounted, and reveals `.rv` elements as they scroll in.
 */
export function useFfl<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    root.classList.add("js");
    const html = document.documentElement;
    const prevScroll = html.style.scrollBehavior;
    html.style.scrollBehavior = "smooth";

    const items = Array.from(root.querySelectorAll<HTMLElement>(".rv"));
    let io: IntersectionObserver | undefined;
    if ("IntersectionObserver" in window) {
      io = new IntersectionObserver(
        (entries) => {
          entries.forEach((e) => {
            if (e.isIntersecting) {
              e.target.classList.add("in");
              io?.unobserve(e.target);
            }
          });
        },
        { rootMargin: "0px 0px -8% 0px", threshold: 0.06 },
      );
      items.forEach((el) => io!.observe(el));
    } else {
      items.forEach((el) => el.classList.add("in"));
    }
    return () => {
      io?.disconnect();
      html.style.scrollBehavior = prevScroll;
      root.classList.remove("js");
    };
  }, []);
  return ref;
}
