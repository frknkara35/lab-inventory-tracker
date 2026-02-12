import streamlit as st
from streamlit_gsheets import GSheetsConnection
import extra_streamlit_components as stx
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime,timedelta
import time





def force_reload():
    js = "<script>window.parent.location.reload();</script>"
    components.html(js, height=0)

def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

def check_login():
    cookie_user = cookie_manager.get(cookie="lab_user")
    if cookie_user:
        return cookie_user
    st.write("Lütfen giriş yapınız")
    with st.form("login_form"):
        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Parola", type="password")
        submitted = st.form_submit_button("Giriş")
        if submitted:
            valid_users = st.secrets["users"]
            if username in valid_users and valid_users[username] == password:
                expires = datetime.now() + timedelta(365) 
                cookie_manager.set("lab_user", username, expires_at=expires)
                st.success(f"Hoşgeldin {username}")
                time.sleep(0.5)
                force_reload()
            else:
                time.sleep(3)
                st.error("Hatalı Kullanıcı Adı veya Parola")
    return None
    
current_user = check_login()
if not current_user:
    st.stop()
st.sidebar.write(f"👤 **{current_user}**")
if st.sidebar.button("Hesaptan Çık"):
    cookie_manager.set("lab_user", "", expires_at=datetime.now() - timedelta(1))
    st.toast("Lütfen sayfayı yenileyiniz")
    time.sleep(1)
    force_reload()

st.set_page_config(page_title="Lab Takip", page_icon="🧪")
st.title(" Lab Envanter Takip Sistemi ")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Sheet1", ttl=1)
    df_log = conn.read(worksheet="Logs", ttl=1)
except Exception as e:
    st.error(f"Error connecting to sheet: {e}")
    st.stop()

message_container = st.empty()

with st.sidebar:
    
    st.dataframe(df_log)

with st.form("inventory_form"):
    changes_log = []
    updated_quantities = []

    for index, row in df.iterrows():
        
        quantity = row["quantity"]
        threshold = row["threshold"]

        if quantity < threshold:
            
            message_container.warning(f"{row["name"]} miktarı kritik eşik altında! (kritik eşik: {int(threshold)} | miktar: {int(quantity)})", icon="⚠️")

        col1, col2 = st.columns([3, 1]) 
        
        old_qty = row["quantity"]
        with col1:
            if quantity < threshold:
                st.header(f":red[{row["name"]}]")
                st.write(f"Miktar: :red[{int(row["quantity"])}] | Kritik Stok: :red[{int(row["threshold"])}] (Tükeniyor!)")
            else:
                st.header(f"{row["name"]}")
                st.write(f"Miktar: :green[{int(row["quantity"])} {row["unit"]}]   |   Kritik Stok: :red[{int(row["threshold"])}]")
    
        with col2:
            new_qty = st.number_input(
                "Change",
                value=int(row["quantity"]),
                step=1,
                key=f"qty_{index}",
                label_visibility="collapsed")
            
            updated_quantities.append(new_qty)

            if new_qty != old_qty: 
                diff = new_qty - old_qty
                changes_log.append({
                "User":current_user,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Item": row["name"],
                "Change": diff 
                })
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submitted = st.form_submit_button("Değişiklikleri Onayla",use_container_width=True)

    if submitted:
        df["quantity"] = updated_quantities

        if len(changes_log) > 0:
            new_log = pd.DataFrame(changes_log)
            df_log = pd.concat([df_log,new_log],ignore_index=True)
 
        conn.update(worksheet="Logs",data=df_log)
        conn.update(worksheet="Sheet1", data=df)
        
        st.toast("Sistem Güncelleniyor")
        time.sleep(1)
        st.rerun()























