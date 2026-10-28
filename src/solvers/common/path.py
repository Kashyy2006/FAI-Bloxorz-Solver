def reconstruct_actions(
    parent: dict[tuple, tuple | None],
    action_to: dict[tuple, str],
    goal_key: tuple,
  ) -> list[str]:
    actions = []
    seen = set()
    key = goal_key

    while True:
        if key in seen:
            raise ValueError("Cycle in parent chain")
        seen.add(key)
        previous = parent[key]
        if previous is None:
            break
        actions.append(action_to[key])
        key = previous

    actions.reverse()
    return actions