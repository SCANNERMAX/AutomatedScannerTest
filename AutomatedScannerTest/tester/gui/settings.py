from PySide6 import QtCore, QtWidgets, QtGui
import logging

logger = logging.getLogger("SettingsDialog")


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
        logger.debug(f"[SettingsDialog] Initializing SettingsDialog with settings: {settings}")

        main_layout = QtWidgets.QVBoxLayout(self)
        content_layout = QtWidgets.QHBoxLayout()
        self.tree_view = QtWidgets.QTreeView(headerHidden=True)
        self.stacked_widget = QtWidgets.QStackedWidget()
        content_layout.addWidget(self.tree_view)
        content_layout.addWidget(self.stacked_widget)
        content_layout.setStretch(0, 1)
        content_layout.setStretch(1, 2)
        main_layout.addLayout(content_layout)

        # Add Save and Cancel buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_save_clicked)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._populate_tree()
        self.tree_view.selectionModel().currentChanged.connect(self._on_tree_selection_changed)
        logger.debug("[SettingsDialog] SettingsDialog initialized successfully.")

    def _populate_tree(self):
        """
        Populate the tree view with settings groups and create corresponding form pages.

        Retrieves all groups from the QSettings instance, creates a tree item for each group,
        and adds a corresponding form page to the stacked widget for editing the group's settings.
        """
        groups = self.settings.childGroups()
        logger.debug(f"[SettingsDialog] Populating tree with groups: {groups}")
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
        add_group_page = self._create_group_page  # Localize for speed
        for group in groups:
            logger.debug(f"[SettingsDialog] Adding group to tree: {group}")
            item = QtGui.QStandardItem(folder_icon, group)
            items.append(item)
            self.stacked_widget.addWidget(add_group_page(group))
        if items:
            self.tree_model.appendColumn(items)
            self.tree_view.setCurrentIndex(self.tree_model.index(0, 0))
            self.stacked_widget.setCurrentIndex(0)
            logger.debug(f"[SettingsDialog] Tree populated with {len(items)} groups.")
        else:
            logger.warning("[SettingsDialog] No settings groups found to populate tree.")

    def _create_group_page(self, group):
        """
        Create a QWidget page with a form for all keys in the given settings group.

        Args:
            group (str): The settings group name.

        Returns:
            QWidget: The form page for the group.
        """
        logger.debug(f"[SettingsDialog] Creating group page for: {group}")
        self.settings.beginGroup(group)
        keys = self.settings.childKeys()
        logger.debug(f"[SettingsDialog] Group \"{group}\" has keys: {keys}")
        page = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(page)
        add_row = form_layout.addRow
        for key in keys:
            value = self.settings.value(key)
            logger.debug(f"[SettingsDialog] Adding key \"{key}\" with value \"{value}\" to form.")
            line_edit = QtWidgets.QLineEdit(str(value))
            line_edit.setObjectName(key)
            add_row(key, line_edit)
        self.settings.endGroup()
        logger.debug(f"[SettingsDialog] Group page created for \"{group}\".")
        return page

    def _on_tree_selection_changed(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex):
        """
        Slot called when a group is selected in the tree view.

        Args:
            current (QModelIndex): The new selected index.
            previous (QModelIndex): The previously selected index.
        """
        idx = current.row()
        logger.debug(f"[SettingsDialog] Tree selection changed from row {previous.row()} to row {idx}.")
        if 0 <= idx < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(idx)
            logger.debug(f"[SettingsDialog] Switched to group page at index {idx}.")
        else:
            logger.warning(f"[SettingsDialog] Invalid tree selection index: {idx}")

    def _on_save_clicked(self):
        """
        Save all changes from the form widgets to QSettings and close the dialog.

        Iterates through all form pages, retrieves the edited values, updates the QSettings instance,
        and emits the settingsModified signal if present before closing the dialog.
        """
        groups = self.settings.childGroups()
        logger.debug(f"[SettingsDialog] Saving settings for groups: {groups}")
        for i, group in enumerate(groups):
            self.settings.beginGroup(group)
            page = self.stacked_widget.widget(i)
            layout = page.layout()
            for j in range(layout.rowCount()):
                label = layout.itemAt(j, QtWidgets.QFormLayout.LabelRole).widget()
                line_edit = layout.itemAt(j, QtWidgets.QFormLayout.FieldRole).widget()
                key = label.text()
                value = line_edit.text()
                logger.debug(f"[SettingsDialog] Setting value for group \"{group}\", key \"{key}\": {value}")
                self.settings.setValue(key, value)
            self.settings.endGroup()
        self.settings.sync()
        logger.debug("[SettingsDialog] Settings saved and synced.")
        # Emit settingsModified if it exists as a Qt signal
        signal = getattr(self.settings, "settingsModified", None)
        if callable(signal):
            logger.debug("[SettingsDialog] Emitting settingsModified signal.")
            signal.emit()
        self.accept()
        logger.debug("[SettingsDialog] SettingsDialog accepted and closed.")