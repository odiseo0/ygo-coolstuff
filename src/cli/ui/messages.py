from textual.message import Message


class NavigateRequested(Message):
    def __init__(self, screen_id: str) -> None:
        self.screen_id = screen_id
        super().__init__()


class SearchSubmitted(Message):
    def __init__(self, query: str) -> None:
        self.query = query
        super().__init__()


class SelectionToggled(Message):
    pass


class AddSelectedRequested(Message):
    pass


class UndoRequested(Message):
    pass


class BackRequested(Message):
    pass


class SearchInputFocused(Message):
    pass


class ImportRequested(Message):
    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__()


class CollectionLoadRequested(Message):
    def __init__(self, collection_id: int) -> None:
        self.collection_id = collection_id
        super().__init__()


class CollectionSaveRequested(Message):
    pass
