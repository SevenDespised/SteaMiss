from __future__ import annotations

from typing import Callable, Iterable, Optional, Union


class MenuComposer:
    """
    菜单组装器（纯聚合器）：
    - 不负责创建/持有具体 builder；
    - 不内置排序规则；
    - 只负责调用 providers 收集菜单项，并按注入的 layout_keys 输出固定扇区列表。
    """

    MenuItem = dict
    ProviderResult = Union[None, MenuItem, list[MenuItem], tuple[MenuItem, ...]]
    Provider = Callable[[], ProviderResult]

    def __init__(
        self,
        providers: Iterable[Provider],
        layout_keys: list[str],
        fill_to: Optional[int] = None,
    ):
        """
        @param providers: provider 列表（建议 provider 内部按需创建 builder 并立即 build，避免复用可变 builder 导致陈旧状态）
        @param layout_keys: 菜单扇区 key 顺序（完全由顶层注入，composer 不维护）
        @param fill_to: 固定输出长度；默认使用 layout_keys 长度
        """
        self.providers = list(providers)
        self.layout_keys = list(layout_keys)
        self.fill_to = fill_to if fill_to is not None else len(self.layout_keys)

    def compose(self):
        """
        构建排序好的菜单项列表（按 layout_keys 输出；缺失项用 None 填充）。
        """
        items: list[MenuComposer.MenuItem] = []

        for provider in self.providers:
            try:
                result = provider()
            except Exception:
                # provider 出错时不阻塞整个菜单渲染（保持 UI 可用）
                continue

            if result is None:
                continue
            if isinstance(result, dict):
                items.append(result)
                continue
            if isinstance(result, (list, tuple)):
                for it in result:
                    if isinstance(it, dict):
                        items.append(it)

        # key -> item（后写覆盖前写，避免重复 key）
        items_map = {item.get("key"): item for item in items if item and item.get("key")}

        output: list[Optional[dict]] = []
        for key in self.layout_keys:
            output.append(items_map.get(key))

        # 若 fill_to > layout_keys，则补齐 None
        while len(output) < int(self.fill_to or 0):
            output.append(None)

        # 若 fill_to < layout_keys，则截断
        return output[: int(self.fill_to or len(output))]


__all__ = ["MenuComposer"]


