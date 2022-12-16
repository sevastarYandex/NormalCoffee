import sys
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QDialog, QMessageBox
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel


class CoffeeDialog(QDialog):
    def __init__(self, varieties, degrees, makings, storages):
        super().__init__()
        uic.loadUi('addEditCoffeeForm.ui', self)
        self.varietyBox.addItems(varieties)
        self.degreeBox.addItems(degrees)
        self.makingBox.addItems(makings)
        self.storageBox.addItems(storages)
        self.ready = False
        self.actionBut.clicked.connect(self.acting)

    def acting(self):
        variety = self.varietyBox.currentText()
        degree = self.degreeBox.currentText()
        making = self.makingBox.currentText()
        storage = self.storageBox.currentText()
        taste = self.tasteEdit.text()
        price = self.priceBox.value()
        size = self.sizeBox.value()
        self.ready = (variety, degree, making, storage, taste, price, size)
        self.close()


class AddCoffeeDialog(CoffeeDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Добавить запись')
        self.actionBut.setText('Добавить запись')


class EditCoffeeDialog(CoffeeDialog):
    def __init__(self, info, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Изменить запись')
        self.actionBut.setText('Изменить запись')
        self.varietyBox.setCurrentText(info[0])
        self.degreeBox.setCurrentText(info[1])
        self.makingBox.setCurrentText(info[2])
        self.storageBox.setCurrentText(info[3])
        self.tasteEdit.setText(info[4])
        self.priceBox.setValue(info[5])
        self.sizeBox.setValue(info[6])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initDB()
        self.initUI()

    def updateModel(self):
        req = """SELECT coffee.ID, variety.title, degree.title, making.title, 
        coffee.storage, coffee.taste, coffee.price, coffee.size FROM 
        coffee INNER JOIN variety INNER JOIN degree INNER JOIN making ON 
        coffee.varietyID = variety.ID AND coffee.degreeID = degree.ID AND
        coffee.makingID = making.ID ORDER BY coffee.ID ASC"""
        self.model.setQuery(self.db.exec(req))

    def initDB(self):
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('coffee.sqlite')
        self.db.open()
        self.model = QSqlQueryModel(self)
        self.updateModel()
        self.TITLES = ['ИД', 'Сорт кофе', 'Степень обжарки',
                       'Вид напитка', 'Хранение',
                       'Вкус', 'Цена за 1 упаковку (в рублях)',
                       'Объём 1 упаковки (в мл)']
        for i in range(len(self.TITLES)):
            self.model.setHeaderData(i, Qt.Orientation.Horizontal, self.TITLES[i])
        varietyReq = self.db.exec("""SELECT title FROM variety""")
        self.VARIETIES = []
        while varietyReq.next():
            self.VARIETIES.append(varietyReq.value(0))
        degreeReq = self.db.exec("""SELECT title FROM degree""")
        self.DEGREES = []
        while degreeReq.next():
            self.DEGREES.append(degreeReq.value(0))
        makingReq = self.db.exec("""SELECT title FROM making""")
        self.MAKINGS = []
        while makingReq.next():
            self.MAKINGS.append(makingReq.value(0))
        self.STORAGES = ['beans', 'ground']

    def initUI(self):
        uic.loadUi('main.ui', self)
        self.view.setModel(self.model)
        self.widget = QWidget()
        self.setCentralWidget(self.widget)
        self.widget.setLayout(self.layout)
        self.addBut.clicked.connect(self.adding)
        self.editBut.clicked.connect(self.editing)

    def adding(self):
        req = AddCoffeeDialog(self.VARIETIES, self.DEGREES,
                              self.MAKINGS, self.STORAGES)
        req.exec()
        ans = req.ready
        if not ans:
            self.statusBar().showMessage('Окно для добавления '
                                         'записей было закрыто')
            return
        variety, degree, making, storage, taste, price, size = ans
        varietyReq = self.db.exec("""SELECT id FROM variety WHERE title IS '""" +
                                  variety + """'""")
        varietyReq.next()
        variety = varietyReq.value(0)
        degreeReq = self.db.exec("""SELECT id FROM degree WHERE title IS '""" +
                                  degree + """'""")
        degreeReq.next()
        degree = degreeReq.value(0)
        makingReq = self.db.exec("""SELECT id FROM making WHERE title IS '""" +
                                  making + """'""")
        makingReq.next()
        making = makingReq.value(0)
        ans = (variety, degree, making, storage, taste, price, size)
        self.db.exec("""INSERT INTO coffee(varietyID, degreeID, makingID, 
        storage, taste, price, size) VALUES""" + str(ans))
        self.statusBar().showMessage('Запись успешно добавлена')
        self.db.commit()
        self.updateModel()

    def editing(self):
        selected = list(set(map(lambda x: x.row(),
                                self.view.selectedIndexes())))
        if len(selected) > 1:
            self.statusBar().showMessage('Ошибка: нельзя одновременно'
                                         ' редактировать более одной записи')
            return
        if not selected:
            self.statusBar().showMessage('Ошибка: не выбрана запись '
                                         'для редактирования')
            return
        id = self.model.index(selected[0], 0).data()
        req = self.db.exec("""SELECT variety.title, degree.title, making.title, 
        coffee.storage, coffee.taste, coffee.price, coffee.size FROM coffee 
        INNER JOIN variety INNER JOIN degree INNER JOIN making ON 
        variety.id = coffee.varietyID AND degree.id = coffee.degreeID 
        AND making.ID = coffee.makingID WHERE coffee.id = """ + str(id))
        req.next()
        info = [req.value(i) for i in range(len(self.TITLES) - 1)]
        req = EditCoffeeDialog(info, self.VARIETIES, self.DEGREES,
                               self.MAKINGS, self.STORAGES)
        req.exec()
        ans = req.ready
        if not ans:
            self.statusBar().showMessage('Окно для редактирования '
                                         'записей было закрыто')
            return
        variety, degree, making, storage, taste, price, size = ans
        varietyReq = self.db.exec("""SELECT id FROM variety WHERE title IS '""" +
                                  variety + """'""")
        varietyReq.next()
        variety = varietyReq.value(0)
        degreeReq = self.db.exec("""SELECT id FROM degree WHERE title IS '""" +
                                 degree + """'""")
        degreeReq.next()
        degree = degreeReq.value(0)
        makingReq = self.db.exec("""SELECT id FROM making WHERE title IS '""" +
                                 making + """'""")
        makingReq.next()
        making = makingReq.value(0)
        self.db.exec("""UPDATE coffee SET varietyID = """ + str(variety) + """, 
        degreeID = """ + str(degree) + """, makingID = """ + str(making) + """, 
        storage = '""" + storage + """', taste = '""" + taste + """', 
        price = """ + str(price) + """, size = """ + str(size) + """ WHERE id = """ + str(id))
        self.statusBar().showMessage('Запись успешно обновлена')
        self.db.commit()
        self.updateModel()

    def closeEvent(self, a0) -> None:
        valid = QMessageBox.question(self, 'Закрыть окно',
                                     'Вы действительно хотите закрыть окно?',
                                     QMessageBox.StandardButton.Yes,
                                     QMessageBox.StandardButton.No)
        if valid != QMessageBox.StandardButton.Yes:
            a0.ignore()
            return
        self.db.close()
        a0.accept()
        super().closeEvent(a0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
