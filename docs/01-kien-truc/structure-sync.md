# Structure Sync Rules

Level: MANDATORY.

Rule: Quan ly va duy tri file tai lieu cau truc thu muc tai `docs/01-kien-truc/structure.md`.

## 1. Khi khoi tao

- Quet toan bo project hien tai, bo qua cac thu muc khong can thiet: `.git`, `node_modules`, `venv`, `__pycache__`, `.idea`, `.vscode`, `dist`, `build`.
- Dung cay thu muc truc quan dang text tree (`├──`, `└──`).
- Chu thich vai tro/chuc nang chinh cua tung thu muc va file quan trong.

## 2. Quy tac tu dong cap nhat Trigger

- Moi khi tao moi thu muc, doi ten, di chuyen hoac xoa thu muc/file module quan trong, PHAI cap nhat ngay file `structure.md` trong cung phien lam viec.
- Neu them thu muc moi, phai bo sung 1 dong chu thich ro chuc nang cua thu muc do.
- Khong de cau truc trong tai lieu bi lech so voi cau truc thu muc thuc te cua code.
- Sau khi cap nhat, thong bao ngan gon 1 dong cho user: `Structure: <ten thu muc/file> -> <thao tac (tao moi/cap nhat/xoa)>`.

