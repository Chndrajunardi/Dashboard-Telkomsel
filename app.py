import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error

# ==========================================
# 1. KONFIGURASI HALAMAN & UI
# ==========================================
st.set_page_config(
    page_title="Telkomsel Dashboard 2025", 
    page_icon="logo.png", 
    layout="wide"
)

def inject_custom_css():
    st.markdown("""
        <style>
        .main { background-color: #f5f7f9; }
        [data-testid="stMetric"] {
            background-color: #1e1e1e;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid #333;
        }
        [data-testid="stMetricLabel"] { color: #ffffff !important; }
        [data-testid="stMetricValue"] { color: #ff4b4b !important; }
        [data-testid="stSidebar"] img {
            display: block;
            margin-left: auto;
            margin-right: auto;
            margin-top: -20px;
        }
        </style>
        """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# 2. DATA ENGINE (LOAD & ML)
# ==========================================
@st.cache_data
def load_master_data():
    try:
        df = pd.read_csv('dashboard_master_data.csv')
        # Pembersihan data (Trimming spasi dan pengisian data kosong)
        df.columns = df.columns.str.strip()
        df = df.fillna(0)
        
        if 'week' not in df.columns:
            df['week'] = np.random.choice(['Week 1', 'Week 2', 'Week 3', 'Week 4'], size=len(df))
        
        # Konversi tanggal yang aman
        df['date'] = pd.to_datetime(df['bulan'] + '-01', errors='coerce')
        return df
    except Exception as e:
        st.error(f"Gagal memuat file CSV: {e}")
        return pd.DataFrame()

def run_ai_forecast(df_input, period='Bulanan'):
    freq_map = {'Mingguan': 'W', 'Bulanan': 'ME', 'Tahunan': 'YE'}
    f = freq_map.get(period, 'ME')
    
    # Resample data
    df_resampled = df_input.groupby(pd.Grouper(key='date', freq=f))['total_revenue'].sum().reset_index()
    df_resampled = df_resampled[df_resampled['total_revenue'] > 0]
    df_resampled['step'] = range(1, len(df_resampled) + 1)
    
    if len(df_resampled) < 2: return df_resampled, 0, 0, 0

    # Model Training
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    X = df_resampled[['step']]
    y = df_resampled['total_revenue']
    model.fit(X, y)
    
    # Metrik Akurasi
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    # Prediksi Masa Depan
    prediction = model.predict([[len(df_resampled) + 1]])[0]
    return df_resampled, prediction, r2, mae

df = load_master_data()

# ==========================================
# 3. SIDEBAR & GLOBAL FILTERS
# ==========================================
if not df.empty:
    with st.sidebar:
        side_col1, side_col2, side_col3 = st.columns([1, 5, 1])
        with side_col2:
            # Fallback jika logo2.png tidak ada
            try: st.image("logo2.png", use_container_width=True)
            except: st.title("TELKOMSEL")
        
        st.title("Navigasi Utama")
        page = st.radio("Pilih Halaman:", ["Dashboard Utama", "Top & Worst Products", "AI Sales Forecast", "Raw Data Explorer"])
        
        st.divider()
        st.header("Filter Waktu")
        month_list = sorted(df['bulan'].unique())
        selected_month = st.selectbox("Pilih Bulan:", month_list, index=len(month_list)-1)
        selected_week = st.selectbox("Pilih Minggu:", ['All Weeks', 'Week 1', 'Week 2', 'Week 3', 'Week 4'])

    # Masking Data
    mask = (df['bulan'] == selected_month)
    if selected_week != 'All Weeks':
        mask &= (df['week'] == selected_week)
    filtered_df = df[mask]

    # ==========================================
    # 4. ROUTING HALAMAN
    # ==========================================

    # --- PAGE: DASHBOARD UTAMA (FULL YEAR) ---
    if page == "Dashboard Utama":
        st.title("Telkomsel Executive Performance 2025")
        st.caption("Analisis Performa Tahunan (Januari - Desember 2025)")

        st.divider()
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Revenue Full Year", f"Rp {df['total_revenue'].sum():,.0f}")
        kpi2.metric("Total Transactions Full Year", f"{df['total_trx'].sum():,.0f}")
        kpi3.metric("Avg. Monthly Active Users", f"{df.groupby('bulan')['active_users'].sum().mean():,.0f}")

        st.divider()
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            rev_trend = df.groupby('bulan')['total_revenue'].sum().reset_index()
            fig_rev = px.line(rev_trend, x='bulan', y='total_revenue', markers=True, color_discrete_sequence=['#ED1C24'], title="Revenue Growth 2025")
            st.plotly_chart(fig_rev, use_container_width=True)
        with t_col2:
            user_trend = df.groupby('bulan')['active_users'].sum().reset_index()
            fig_user = px.line(user_trend, x='bulan', y='active_users', markers=True, color_discrete_sequence=['#A7191D'], title="User Engagement 2025")
            st.plotly_chart(fig_user, use_container_width=True)

        st.divider()
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            branch_data = df.groupby('BRANCH')['total_revenue'].sum().sort_values(ascending=True).tail(10).reset_index()
            fig_branch = px.bar(branch_data, x='total_revenue', y='BRANCH', orientation='h', color='total_revenue', color_continuous_scale='Reds', title="Top 10 Branch Performance")
            st.plotly_chart(fig_branch, use_container_width=True)
        with r_col2:
            chan_data = df.groupby('channel_new')['total_revenue'].sum().reset_index()
            fig_chan = px.pie(chan_data, values='total_revenue', names='channel_new', hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r, title="Channel Contribution")
            st.plotly_chart(fig_chan, use_container_width=True)

    # --- PAGE: TOP & WORST PRODUCTS ---
    elif page == "Top & Worst Products":
        st.title("Product Ranking Analysis")
        st.caption(f"Filter aktif: {selected_month} | {selected_week}")
        
        prod_agg = filtered_df.groupby('package_category').agg({'total_revenue':'sum', 'total_trx':'sum'}).reset_index()
        metric = st.segmented_control("Pilih Metrik:", ["total_revenue", "total_trx"], default="total_revenue")
        
        # INSIGHT OTOMATIS
        st.divider()
        i_col1, i_col2 = st.columns(2)
        top_row = prod_agg.sort_values(metric, ascending=False).iloc[0]
        i_col1.info(f"**Dominasi Produk:** {top_row['package_category']} menyumbang kontribusi terbesar pada filter ini.")
        i_col2.warning(f"**Analisis Efisiensi:** Terdapat {len(prod_agg[prod_agg[metric] < prod_agg[metric].median()])} produk di bawah performa rata-rata.")

        tab_top, tab_worst = st.tabs(["Top 20 Best", "Top 20 Worst"])
        with tab_top:
            top_df = prod_agg.sort_values(metric, ascending=False).head(20)
            fig_top = px.bar(top_df, x=metric, y='package_category', orientation='h', color=metric, color_continuous_scale='Reds')
            st.plotly_chart(fig_top, use_container_width=True)
        with tab_worst:
            worst_df = prod_agg[prod_agg[metric] > 0].sort_values(metric, ascending=True).head(20)
            fig_worst = px.bar(worst_df, x=metric, y='package_category', orientation='h', color=metric, color_continuous_scale='Reds_r')
            st.plotly_chart(fig_worst, use_container_width=True)

    # --- PAGE: AI SALES FORECAST ---
    elif page == "AI Sales Forecast":
        st.title("🤖 AI-Powered Revenue Forecasting")
        st.caption("Prediksi Machine Learning menggunakan algoritma Random Forest Regressor")
        
        period_choice = st.radio("Pilih Skala Waktu Prediksi:", ["Mingguan", "Bulanan", "Tahunan"], horizontal=True)
        
        # Menjalankan Engine ML
        df_resampled, prediction, r2, mae = run_ai_forecast(df, period_choice)
        
        if prediction > 0:
            st.divider()
            f_col1, f_col2 = st.columns([2, 1])
            
            with f_col1:
                st.subheader(f"Grafik Tren & Proyeksi {period_choice}")
                
                # Persiapan Data Visualisasi
                plot_df = df_resampled.copy()
                plot_df['label'] = plot_df['date'].dt.strftime('%Y-%m-%d')
                
                # Menghitung Tanggal Prediksi Berikutnya secara dinamis
                if period_choice == "Mingguan": 
                    next_date = plot_df['date'].max() + pd.Timedelta(weeks=1)
                elif period_choice == "Tahunan": 
                    next_date = plot_df['date'].max() + pd.DateOffset(years=1)
                else: 
                    next_date = plot_df['date'].max() + pd.DateOffset(months=1)
                    
                new_row = pd.DataFrame({
                    'date': [next_date], 
                    'total_revenue': [prediction], 
                    'label': ["Next Period (AI)"]
                })
                full_df = pd.concat([plot_df, new_row], ignore_index=True)
                
                # Plotly Chart
                fig_ai = px.line(full_df, x='label', y='total_revenue', markers=True, 
                                  color_discrete_sequence=['#ED1C24'], template="plotly_white")
                
                # Tambahkan Marker Khusus Prediksi (Bintang Emas)
                fig_ai.add_scatter(x=["Next Period (AI)"], y=[prediction], mode='markers', 
                                   marker=dict(size=18, color='gold', symbol='star', line=dict(width=2, color='black')),
                                   name='Target Prediksi AI')
                
                st.plotly_chart(fig_ai, use_container_width=True)

                # --- INSIGHT: EVALUASI VALIDITAS ---
                with st.expander("🔍 Analisis Validitas Model (Data Science Insight)"):
                    m_col1, m_col2 = st.columns(2)
                    m_col1.metric("Model Accuracy (R²)", f"{r2*100:.1f}%")
                    m_col2.metric("Avg. Prediction Error", f"Rp {mae:,.0f}")
                    st.write(f"""
                    **Interpretasi:** Model memiliki tingkat kepercayaan sebesar **{r2*100:.1f}%**. 
                    Angka MAE menunjukkan bahwa prediksi memiliki margin error rata-rata sebesar ±Rp {mae:,.0f} 
                    berdasarkan deviasi data historis.
                    """)

            with f_col2:
                st.subheader("Executive Interpretation")
                
                # Kalkulasi Growth
                last_actual = df_resampled['total_revenue'].iloc[-1]
                growth_pct = ((prediction - last_actual) / last_actual) * 100
                
                st.metric("Estimasi Revenue Mendatang", f"Rp {prediction:,.0f}", delta=f"{growth_pct:.1f}%")
                
                st.divider()
                
                # --- AUTO-INSIGHT & STRATEGY ---
                if growth_pct > 0:
                    st.success("🚀 **Sinyal Pertumbuhan Terdeteksi**")
                    st.write(f"""
                    **Analisis:** AI memprediksi kenaikan sebesar **{growth_pct:.1f}%**. Ini menandakan momentum 
                    pasar yang kuat untuk periode mendatang.
                    
                    **Rekomendasi Strategis:**
                    1. **Upselling:** Luncurkan kampanye promo paket data premium untuk memaksimalkan ARPU.
                    2. **Stock Readiness:** Pastikan ketersediaan stok voucher digital di seluruh channel distribusi.
                    3. **Network Ops:** Optimalkan kapasitas jaringan di area dengan trafik transaksi tertinggi.
                    """)
                else:
                    st.error("⚠️ **Waspada Koreksi Musiman**")
                    st.write(f"""
                    **Analisis:** AI mendeteksi potensi penurunan sebesar **{abs(growth_pct):.1f}%**. 
                    Kondisi ini umum terjadi sebagai fase normalisasi pasca-peak season.
                    
                    **Rekomendasi Strategis:**
                    1. **Retention:** Fokus pada program loyalitas untuk mencegah 'churn' pelanggan high-value.
                    2. **Efficiency:** Tinjau kembali biaya akuisisi pada channel dengan konversi rendah.
                    3. **Churn Prevention:** Berikan penawaran khusus 'Win-back' bagi pelanggan yang kurang aktif.
                    """)
                
                st.divider()
                st.caption(f"Hasil diolah dari {len(df_resampled)} data point historis.")

        else:
            st.warning("Data tidak mencukupi untuk melakukan peramalan (Forecasting).")

    # --- PAGE: RAW DATA EXPLORER ---
    else:
        st.title("Raw Data Explorer")
        st.write(f"Menampilkan {len(filtered_df)} baris data hasil filter.")
        st.dataframe(filtered_df, use_container_width=True)
else:
    st.warning("Menunggu data CSV diunggah atau diperbaiki...")