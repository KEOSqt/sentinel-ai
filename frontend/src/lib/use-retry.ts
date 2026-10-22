import { useCallback, useState } from "react";

export function useRetry() {
  const [attempt, setAttempt] = useState(0);
  const retry = useCallback(() => setAttempt((value) => value + 1), []);
  return { attempt, retry };
}
