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
        self.tree_view.header().hide()
        self.stacked_widget = QtWidgets.QStackedWidget()
        content_layout.addWidget(self.tree_view)
        content_layout.addWidget(self.stacked_widget)
        # Set stretch: left (tree_view) is 1, right (stacked_widget) is 2
        content_layout.setStretch(0, 1)
        content_layout.setStretch(1, 2)
        main_layout.addLayout(content_layout)

        # Add Save and Cancel buttons
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_save_clicked)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._populate_tree()
        self.tree_view.clicked.connect(self._on_tree_clicked)

    def _populate_tree(self):
        """
        Populate the tree view with settings groups and create corresponding form pages.
        """
        groups = self.settings.childGroups()
        # Use QStandardItemModel to support icons
        self.tree_model = QtGui.QStandardItemModel()
        self.tree_view.setModel(self.tree_model)
        self.tree_model.setHorizontalHeaderLabels(["Groups"])

        # Use a standard folder icon from the style
        folder_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)

        # Clear stacked widget pages
        for i in reversed(range(self.stacked_widget.count())):
            widget = self.stacked_widget.widget(i)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()

        for group in groups:
            item = QtGui.QStandardItem(folder_icon, group)
            self.tree_model.appendRow(item)
            self.stacked_widget.addWidget(self._create_group_page(group))

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

    def _on_tree_clicked(self, index: QtCore.QModelIndex):
        """
        Slot called when a group is selected in the tree view.

        Args:
            index (QModelIndex): The index of the selected group.
        """
        if 0 <= index.row() < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index.row())

    def _on_save_clicked(self):
        """
        Save all changes from the form widgets to QSettings and close the dialog.
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
        if hasattr(self.settings, "settingsModified"):
            self.settings.settingsModified.emit()
        self.accept()