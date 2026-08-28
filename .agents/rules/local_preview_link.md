# Project Instructions & Workspace Rules (newsl)

## 📌 ขอบเขตการทำงาน (Workspace Scope)
- เมื่อทำงานในโฟลเดอร์ **newsl** ให้ทำงานและแก้ไขเฉพาะส่วนภายในโฟลเดอร์ **newsl** เท่านั้น ไม่แตะต้องโปรเจกต์ภายนอก

## 🚫 ข้อห้ามการ Upload GitHub อัตโนมัติ (No Auto GitHub Push)
- **ห้ามทำการ push หรือ upload ขึ้น GitHub โดยเด็ดขาด** ในระหว่างการแก้ไขหรือพัฒนา
- ให้ทำงานและทดสอบผลลัพธ์บนเครื่อง Local ให้เรียบร้อยก่อน
- จะทำการ push/upload ขึ้น GitHub ได้ก็ต่อเมื่อได้รับคำสั่งจากผู้ใช้ให้ Upload เท่านั้น

## ⚙️ ข้อควรระวังความเข้ากันได้ระหว่าง Local & Streamlit Cloud (Compatibility Guard)
- **ห้ามฮาร์ดโค้ด `port` ใน `.streamlit/config.toml` โดยเด็ดขาด**: เพราะจะทำให้ Streamlit Cloud เชื่อมต่อไม่ติด (Healthcheck failed / "Oh no. Error running app.")
- การรันบน Local ให้ใช้พอร์ต 8502 ผ่านพารามิเตอร์คำสั่ง เช่น `streamlit run app.py --server.port 8502` เท่านั้น

## 🔗 กฎการส่งลิงก์สำหรับเปิดดูผลลัพธ์ (Preview Links Workflow)
1. **เมื่อแก้ไข/พัฒนาบนเครื่อง Local**:
   - ให้สร้าง/แนบลิงก์ทดสอบ Local Port 8502: 👉 [http://localhost:8502](http://localhost:8502)
2. **เมื่อได้รับคำสั่งและทำการ Upload/Push ขึ้น GitHub เรียบร้อยแล้ว**:
   - ให้สร้าง/แนบลิงก์ Streamlit Cloud Production: 👉 [https://newslite.streamlit.app](https://newslite.streamlit.app)
