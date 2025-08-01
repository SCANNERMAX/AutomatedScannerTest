from PySide6 import QtCore, QtWidgets, QtGui

class SettingsDialog(QtWidgets.QDialog):
    """
    Dialog for viewing and editing application settings.

    Displays a tree of settings groups on the left and a stacked widget of editable forms for each group on the right.
    Selecting a group in the tree displays its settings in the form.
    """

    def __init__(self, settings: QtCore.QSettings):
        """
        Initialize the SettingsDialog.

        Args:
            settings (QSettings): The QSettings instance to display and edit.
        """
        super().__init__()
        self.settings = settings
        self.setWindowTitle("Settings Dialog")

        main_layout = QtWidgets.QVBoxLayout(self)
        content_layout = QtWidgets.QHBoxLayout()
        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.stacked_widget = QtWidgets.QStackedWidget()
        content_layout.addWidget(self.tree_view)
        content_layout.addWidget(self.stacked_widget)
        content_layout.setStretch(0, 1)
        content_layout.setStretch(1, 2)
        main_layout.addLayout(content_layout)

        # Add Save and Cancel buttons
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_save_clicked)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._populate_tree()
        self.tree_view.selectionModel().currentChanged.connect(self._on_tree_selection_changed)

    def _populate_tree(self):
        """
        Populate the tree view with settings groups and create corresponding form pages.

        This method retrieves all groups from the QSettings instance, creates a tree item for each group,
        and adds a corresponding form page to the stacked widget for editing the group's settings.
        """
        groups = self.settings.childGroups()
        self.tree_model = QtGui.QStandardItemModel()
        self.tree_view.setModel(self.tree_model)
        self.tree_model.setHorizontalHeaderLabels(["Groups"])
        folder_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)

        # Efficiently clear stacked widget pages
        while self.stacked_widget.count():
            widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()

        items = []
        for group in groups:
            item = QtGui.QStandardItem(folder_icon, group)
            items.append(item)
            self.stacked_widget.addWidget(self._create_group_page(group))
        if items:
            self.tree_model.appendColumn(items)
            self.tree_view.setCurrentIndex(self.tree_model.index(0, 0))
            self.stacked_widget.setCurrentIndex(0)

    def _create_group_page(self, group):
        """
        Create a QWidget page with a form for all keys in the given settings group.

        Args:
            group (str): The settings group name.

        Returns:
            QWidget: The form page for the group.
        """
        self.settings.beginGroup(group)
        keys = self.settings.childKeys()
        page = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(page)
        for key in keys:
            value = self.settings.value(key)
            line_edit = QtWidgets.QLineEdit(str(value))
            line_edit.setObjectName(key)
            form_layout.addRow(key, line_edit)
        self.settings.endGroup()
        return page

    def _on_tree_selection_changed(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex):
        """
        Slot called when a group is selected in the tree view.

        Args:
            current (QModelIndex): The new selected index.
            previous (QModelIndex): The previously selected index.
        """
        idx = current.row()
        if 0 <= idx < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(idx)

    def _on_save_clicked(self):
        """
        Save all changes from the form widgets to QSettings and close the dialog.

        This method iterates through all form pages, retrieves the edited values, updates the QSettings instance,
        and emits the settingsModified signal if present before closing the dialog.
        """
        groups = self.settings.childGroups()
        for i, group in enumerate(groups):
            self.settings.beginGroup(group)
            page = self.stacked_widget.widget(i)
            layout = page.layout()
            for j in range(layout.rowCount()):
                label = layout.itemAt(j, QtWidgets.QFormLayout.LabelRole).widget()
                line_edit = layout.itemAt(j, QtWidgets.QFormLayout.FieldRole).widget()
                key = label.text()
                value = line_edit.text()
                self.settings.setValue(key, value)
            self.settings.endGroup()
        self.settings.sync()
        # Emit settingsModified if it exists as a Qt signal
        signal = getattr(self.settings, "settingsModified", None)
        if callable(signal):
            signal.emit()
        self.accept()