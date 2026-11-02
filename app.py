import io, math
from collections import Counter
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title='ROULETTE AI', page_icon='🎡', layout='wide')

RED={1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
def color(n): return 'Green' if n==0 else ('Red' if n in RED else 'Black')
def normalize(df):
    cols={str(c).strip().lower():c for c in df.columns}
    col=next((cols[k] for k in ['number','result','spin','winning number','numero','numéro'] if k in cols),None)
    if col is None:
        if len(df.columns)==1: col=df.columns[0]
        else: raise ValueError('The file must contain a column named number (or result).')
    s=pd.to_numeric(df[col],errors='coerce').dropna().astype(int)
    bad=s[(s<0)|(s>36)]
    if len(bad): raise ValueError('European roulette values must be from 0 to 36.')
    return s.reset_index(drop=True)

if 'spins' not in st.session_state: st.session_state.spins=[]
spins=st.session_state.spins
st.title('🎡 ROULETTE AI')
st.caption('European roulette • Historical data • Statistical analysis • Mobile-friendly dashboard')
st.warning('Important: on a fair roulette wheel, every spin is independent. Historical patterns do not predict the next result or guarantee profit. This app is for analysis and experimentation, not betting advice.')
with st.sidebar:
    st.header('Navigation')
    page=st.radio('Choose a section',['Dashboard','Enter results','Import CSV / Excel','Image OCR','Video inspection','Statistics','Simulation','Data & export'])
    st.divider()
    st.metric('Stored spins',len(spins))
    if st.button('Clear all data',type='secondary'):
        st.session_state.spins=[]; st.rerun()

if page=='Dashboard':
    st.subheader('Dashboard')
    a,b,c=st.columns(3); a.metric('Total spins',len(spins)); b.metric('Unique numbers',len(set(spins)) if spins else 0); c.metric('Theoretical chance per number','2.70%')
    if spins:
        df=pd.DataFrame({'number':spins}); df['color']=df.number.map(color)
        st.plotly_chart(px.histogram(df,x='number',nbins=37,title='Historical result counts',color='color'),use_container_width=True)
        st.dataframe(df.tail(20).iloc[::-1],use_container_width=True)
    else: st.info('No results yet. Add results manually or import a file.')
elif page=='Enter results':
    st.subheader('Enter roulette results')
    raw=st.text_area('Enter numbers separated by commas, spaces, or new lines',placeholder='17, 0, 32, 5, 19')
    if st.button('Add results',type='primary'):
        try:
            vals=[int(x) for x in raw.replace(',', ' ').split()]
            if not vals or any(x<0 or x>36 for x in vals): raise ValueError()
            spins.extend(vals); st.success(f'Added {len(vals)} results.'); st.rerun()
        except: st.error('Enter whole numbers from 0 to 36.')
elif page=='Import CSV / Excel':
    st.subheader('Import historical results')
    f=st.file_uploader('Choose CSV or Excel file',type=['csv','xlsx','xls'])
    if f:
        try:
            d=pd.read_csv(f) if f.name.lower().endswith('.csv') else pd.read_excel(f)
            st.dataframe(d.head(10),use_container_width=True)
            vals=normalize(d).tolist()
            if st.button(f'Import {len(vals)} results',type='primary'):
                spins.extend(vals); st.success('Imported successfully.'); st.rerun()
        except Exception as e: st.error(str(e))
elif page=='Image OCR':
    st.subheader('Read numbers from a screenshot')
    st.caption('OCR is experimental. Always review recognized numbers before using them.')
    f=st.file_uploader('Upload screenshot',type=['png','jpg','jpeg'])
    if f:
        st.image(f,use_container_width=True)
        try:
            from PIL import Image
            import pytesseract
            text=pytesseract.image_to_string(Image.open(f),config='--psm 6')
            found=[int(x) for x in __import__('re').findall(r'(?<!\d)(?:[0-9]|[123][0-9])(?!\d)',text) if int(x)<=36]
            st.write('Recognized text:',text or '(none)')
            st.write('Possible results:',found)
            edited=st.text_input('Correct the results if needed (comma-separated)',','.join(map(str,found)))
            if st.button('Add reviewed results'):
                vals=[int(x.strip()) for x in edited.split(',') if x.strip()]
                if any(x<0 or x>36 for x in vals): st.error('Values must be 0–36.')
                else: spins.extend(vals); st.success(f'Added {len(vals)} results.'); st.rerun()
        except Exception as e: st.error('OCR is unavailable on this deployment. You can still import CSV/Excel or enter results manually.')
elif page=='Video inspection':
    st.subheader('Video inspection')
    st.info('This section is a basic upload/inspection placeholder. It does not measure a roulette ball or calculate reliable landing predictions.')
    v=st.file_uploader('Upload a short roulette video',type=['mp4','mov','avi'])
    if v:
        st.video(v)
        st.caption('Video uploaded for visual review. No result is inferred automatically.')
elif page=='Statistics':
    st.subheader('Statistical analysis')
    if not spins: st.info('Add or import results first.')
    else:
        n=len(spins); counts=pd.Series(spins).value_counts().reindex(range(37),fill_value=0)
        table=pd.DataFrame({'Number':range(37),'Color':[color(i) for i in range(37)],'Count':counts.values,'Observed %':counts.values/n*100,'Expected %':[100/37]*37})
        st.plotly_chart(px.bar(table,x='Number',y='Count',color='Color',title=f'Number frequency ({n} spins)'),use_container_width=True)
        st.dataframe(table.sort_values('Count',ascending=False),use_container_width=True)
        observed=np.array(counts.values,dtype=float); expected=np.full(37,n/37)
        chi=float(((observed-expected)**2/expected).sum()) if n else 0
        st.metric('Chi-square statistic',f'{chi:.2f}')
        st.caption('A frequency difference in a finite sample can occur by chance; it does not establish an exploitable bias.')
        colors=pd.Series([color(x) for x in spins]).value_counts().reindex(['Red','Black','Green'],fill_value=0).reset_index(); colors.columns=['Color','Count']
        st.plotly_chart(px.pie(colors,names='Color',values='Count',title='Color distribution'),use_container_width=True)
elif page=='Simulation':
    st.subheader('Fair-wheel simulation')
    n=st.slider('Number of simulated spins',100,100000,5000,100)
    if st.button('Run simulation',type='primary'):
        rng=np.random.default_rng(); sim=rng.integers(0,37,n); cnt=pd.Series(sim).value_counts().reindex(range(37),fill_value=0)
        d=pd.DataFrame({'Number':range(37),'Count':cnt.values})
        st.plotly_chart(px.bar(d,x='Number',y='Count',title=f'{n:,} simulated fair spins'),use_container_width=True)
        st.write(f'Expected average per number: {n/37:.1f}. Actual range: {cnt.min()}–{cnt.max()}.')
elif page=='Data & export':
    st.subheader('Data management')
    if spins:
        d=pd.DataFrame({'number':spins,'color':[color(x) for x in spins]})
        st.dataframe(d,use_container_width=True)
        st.download_button('Download results as CSV',d.to_csv(index=False).encode(),file_name='roulette_results.csv',mime='text/csv')
    else: st.info('No data to export yet.')
    st.caption('Data is kept in the current app session. Download your CSV regularly to keep a copy.')

st.divider(); st.caption('ROULETTE AI • Statistical research tool • European wheel (0–36)')
