import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title='GS건설 재무흐름 분석', page_icon='🏗️', layout='wide')

# -----------------------------
# Data: supplied GS E&C IR / DART disclosures
# Unit: KRW bn unless otherwise stated
# -----------------------------
annual = pd.DataFrame({
    '연도':['2023','2024','2025'],
    '신규수주':[13430.0,19910.0,19207.3],
    '매출':[13436.7,12863.8,12450.3],
    '매출총이익':[262.2,1114.2,1345.1],
    '영업이익':[-387.9,286.0,437.8],
    '영업현금흐름':[469.799,267.812,591.530],
})
annual['GPM(%)'] = annual['매출총이익']/annual['매출']*100
annual['영업이익률(%)'] = annual['영업이익']/annual['매출']*100
annual['영업현금흐름/영업이익'] = annual.apply(lambda r: None if r['영업이익'] <= 0 else r['영업현금흐름']/r['영업이익'], axis=1)

sales = pd.DataFrame({
    '사업':['건축·주택','신사업/ABED','플랜트','인프라','그린','기타'],
    '2023':[10237.1,1414.4,300.5,1104.1,271.8,108.8],
    '2024':[9510.9,1392.1,701.7,1153.5,0.0,105.5],
    '2025':[7786.9,1778.7,1320.1,1461.4,0.0,103.2],
})

# 2024/2025 order backlog. 2025 format merges Green into Plant/Infra.
backlog = pd.DataFrame({
    '사업':['건축·주택','신사업/ABED','플랜트','인프라'],
    '2024':[32613.3,17082.4,4895.1,5892.7],
    '2025':[40668.0,20320.4,3893.9,5678.4],
})

# GPM: annual 2023/2024; 2025 annual division GPM is not disclosed in the supplied annual IR.
gpm = pd.DataFrame({
    '사업':['건축·주택','신사업/ABED','플랜트','인프라','그린','기타'],
    '2023':[-0.3,17.2,-5.5,2.2,11.8,6.7],
    '2024':[9.3,15.6,2.9,-0.7,1.2,7.8],
})

# Latest disclosed quarterly GPM comparison from 1Q26 IR
latest_gpm = pd.DataFrame({
    '사업':['건축·주택','신사업/ABED','플랜트','인프라','기타'],
    '1Q25':[9.5,9.4,2.4,14.8,15.3],
    '4Q25':[17.3,-7.8,14.1,9.0,-1.8],
    '1Q26':[12.4,18.3,-24.2,3.9,10.4],
})

# Unbilled construction by division from IR snapshots (through 3Q24)
unbilled_div = pd.DataFrame({
    '사업':['건축·주택','신사업','플랜트','인프라','그린'],
    '2023':[648,39,132,344,36],
    '1Q24':[672,30,138,351,12],
    '3Q24':[810,30,142,332,23],
})

# 2026 H1 DART: contract assets (unbilled construction) by division
unbilled_26h1 = pd.DataFrame({
    '사업':['건축·주택','플랜트','인프라','신성장사업개발','Inima'],
    '2025말':[724.886,55.367,115.736,2.967,22.358],
    '2026H1':[263.191,47.440,100.817,2.091,33.893],
})

# Company-wide collection indicators from DART (gross amount)
collection = pd.DataFrame({
    '시점':['2024말','2025말','2026H1'],
    '공사미수금':[2439.383,2148.390,2339.230],
    '미청구공사':[1402.696,1063.114,447.432],  # 2026H1 = disclosed divisional contract asset sum before allowance
})

# 2026 H1 cash flow is half-year flow, so kept separate from annual series
h1_2026 = {'매출':5179.903, '영업현금흐름':94.379}

SOURCE_NOTES = {
    '2023 IR':'4Q23_Conference_[Audited].pdf — Order Backlogs, Sales & GPM, Liquidity',
    '2024 IR':'4Q24_Conference_[Audited].pdf — New Orders & Order Backlog, Sales & Profit/Loss, Financial Status',
    '2025 IR':'4Q25_GS E＆C_[Audited].pdf — New Order & Order Backlog, Sales & Profit, Financial Status',
    '2026 1Q IR':'1Q26_GS E＆C_[Audited].pdf — New Order & Order Backlog, Sales/GPM/Profit',
    '2025 사업보고서':'[GS건설][정정]사업보고서(2026.07.01).pdf — 공사미수금·미청구공사·현금흐름',
    '2026 반기보고서':'[GS건설]반기보고서(2026.08.14).pdf — 사업부 매출·계약자산·공사미수금·현금흐름',
}

# -----------------------------
# Helpers
# -----------------------------
def fmt_bn(x):
    return f'{x:,.1f}억원' if x < 1000 else f'{x/1000:,.2f}조원'

def pct_change(a,b):
    return (b/a-1)*100 if a else None

def insight_box(title, lines):
    st.markdown(f'### {title}')
    for line in lines:
        st.markdown(f'- {line}')

# -----------------------------
# Header
# -----------------------------
st.title('🏗️ GS건설 재무흐름 분석 프로그램')
st.caption('핵심 질문: GS건설은 어떤 사업에서 일감을 확보하고, 이를 매출과 이익으로 전환한 뒤 실제 현금까지 잘 회수하고 있는가?')

with st.expander('분석 구조와 데이터 기준'):
    st.markdown('''
**분석 흐름**  
`신규수주 → 수주잔고 → 매출 → 수익성 → 미청구공사·공사미수금 → 영업현금흐름`

- **사업별 분석**: 수주잔고, 매출, GPM을 비교합니다.
- **회수 분석**: 공사미수금과 미청구공사, 영업현금흐름은 연결 기준으로 봅니다.
- 2025년부터 공시 사업구분이 일부 변경되었습니다. Green은 Plant/Infra에 통합됐고, 2026년에는 New Business가 **ABED(Advanced Built Environment Development)**로 표시됩니다.
- 공시에서 제공하지 않는 사업부별 영업현금흐름은 임의 배분하지 않았습니다.
''')

# KPIs
c1,c2,c3,c4 = st.columns(4)
c1.metric('2025 신규수주', '19.21조원', '2024 대비 -3.5%')
c2.metric('2025 수주잔고', '70.56조원', '2024 대비 +11.1%')
c3.metric('2025 매출', '12.45조원', '2024 대비 -3.2%')
c4.metric('2025 영업이익', '4,378억원', '2024 대비 +53.1%')

# -----------------------------
# Tabs
# -----------------------------
t1,t2,t3,t4,t5 = st.tabs(['① 수주 경쟁력','② 매출 전환','③ 수익성','④ 회수·현금','⑤ 최종 진단'])

with t1:
    st.subheader('① 수주 경쟁력 — 앞으로 벌 일감이 어디에 쌓이고 있는가?')
    left,right = st.columns([1.35,1])
    with left:
        long = backlog.melt('사업', var_name='연도', value_name='수주잔고')
        fig = px.bar(long, x='사업', y='수주잔고', color='연도', barmode='group', text_auto='.3s',
                     labels={'수주잔고':'수주잔고 (십억원)'})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        b24 = backlog.set_index('사업')['2024']; b25=backlog.set_index('사업')['2025']
        insight_box('이 탭의 결론', [
            f"건축·주택 수주잔고는 2024년 {b24['건축·주택']/1000:.1f}조원 → 2025년 {b25['건축·주택']/1000:.1f}조원으로 증가했습니다.",
            f"신사업/ABED도 {b24['신사업/ABED']/1000:.1f}조원 → {b25['신사업/ABED']/1000:.1f}조원으로 증가해 두 번째로 큰 일감 축입니다.",
            '따라서 GS건설의 미래 매출 기반은 여전히 건축·주택이 가장 크지만, 신사업도 의미 있는 수주잔고를 확보하고 있습니다.',
            '플랜트·인프라는 수주잔고가 감소했으므로 신규수주가 실제 잔고 보충으로 이어지는지 함께 볼 필요가 있습니다.'
        ])
    st.dataframe(backlog.set_index('사업'), use_container_width=True)

with t2:
    st.subheader('② 매출 전환 — 확보한 일감이 실제 실적으로 이어지는가?')
    long = sales.melt('사업', var_name='연도', value_name='매출')
    fig = px.bar(long, x='사업', y='매출', color='연도', barmode='group', text_auto='.3s',
                 labels={'매출':'매출 (십억원)'})
    st.plotly_chart(fig, use_container_width=True)
    s=sales.set_index('사업')
    insight_box('이 탭의 결론', [
        f"건축·주택 매출은 2023년 {s.loc['건축·주택','2023']/1000:.2f}조원 → 2025년 {s.loc['건축·주택','2025']/1000:.2f}조원으로 감소했습니다.",
        f"반면 신사업/ABED는 {s.loc['신사업/ABED','2023']/1000:.2f}조원 → {s.loc['신사업/ABED','2025']/1000:.2f}조원으로 증가했습니다.",
        f"플랜트도 같은 기간 {s.loc['플랜트','2023']/1000:.2f}조원 → {s.loc['플랜트','2025']/1000:.2f}조원으로 확대됐습니다.",
        '즉 전체 매출이 감소하는 가운데 사업별 매출 구성은 주택 중심에서 신사업·플랜트·인프라 쪽으로 일부 이동하고 있습니다.'
    ])
    st.dataframe(sales.set_index('사업'), use_container_width=True)

with t3:
    st.subheader('③ 수익성 — 매출을 늘리는 것에서 끝나지 않고 얼마나 남기는가?')
    left,right=st.columns(2)
    with left:
        glong=gpm.melt('사업',var_name='연도',value_name='GPM')
        fig=px.bar(glong,x='사업',y='GPM',color='연도',barmode='group',text_auto='.1f',labels={'GPM':'GPM (%)'})
        fig.add_hline(y=0,line_dash='dash')
        st.plotly_chart(fig,use_container_width=True)
        st.caption('2023·2024 연간 사업부별 GPM')
    with right:
        llong=latest_gpm.melt('사업',var_name='시점',value_name='GPM')
        fig=px.bar(llong,x='사업',y='GPM',color='시점',barmode='group',text_auto='.1f',labels={'GPM':'GPM (%)'})
        fig.add_hline(y=0,line_dash='dash')
        st.plotly_chart(fig,use_container_width=True)
        st.caption('1Q25·4Q25·1Q26 사업부별 GPM — 최신 분기 흐름 확인용')
    insight_box('이 탭의 결론', [
        '2023년 건축·주택 GPM은 -0.3%였지만 2024년 9.3%로 회복했습니다.',
        '신사업은 2023년 17.2%, 2024년 15.6%로 상대적으로 높은 연간 GPM을 기록했습니다.',
        '다만 2025년 연간 사업부별 GPM은 제공된 연간 IR에서 동일 형식으로 공시되지 않아 임의 계산하지 않았습니다.',
        '1Q26에는 ABED GPM 18.3%인 반면 플랜트는 -24.2%여서 사업별 수익성 차이가 크게 나타납니다.'
    ])

with t4:
    st.subheader('④ 회수·현금 — 장부상 성과가 실제 현금으로 이어지는가?')
    st.markdown('#### 4-1. 미청구공사: 공사는 했지만 아직 청구하지 못한 금액')
    left,right=st.columns([1.25,1])
    with left:
        ul=unbilled_div.melt('사업',var_name='시점',value_name='미청구공사')
        fig=px.bar(ul,x='사업',y='미청구공사',color='시점',barmode='group',text_auto='.3s',labels={'미청구공사':'미청구공사 (십억원)'})
        st.plotly_chart(fig,use_container_width=True)
    with right:
        st.dataframe(unbilled_26h1.set_index('사업'),use_container_width=True)
        st.caption('2026H1 반기보고서의 사업부별 계약자산(미청구공사). 단위: 십억원')
        insight_box('해석',[
            '2023~3Q24 IR에서는 건축·주택의 미청구공사가 가장 큰 비중을 차지했습니다.',
            '2026H1 공시에서도 사업부별 계약자산을 확인할 수 있어 회수 부담이 어느 사업에 집중되는지 보조적으로 확인할 수 있습니다.'
        ])

    st.markdown('#### 4-2. 회사 전체 공사미수금·미청구공사')
    cl=collection.melt('시점',var_name='항목',value_name='금액')
    fig=px.line(cl,x='시점',y='금액',color='항목',markers=True,text='금액',labels={'금액':'금액 (십억원)'})
    st.plotly_chart(fig,use_container_width=True)

    st.markdown('#### 4-3. 영업현금흐름')
    fig=px.bar(annual,x='연도',y='영업현금흐름',text_auto='.1f',labels={'영업현금흐름':'영업현금흐름 (십억원)'})
    st.plotly_chart(fig,use_container_width=True)
    st.metric('2026H1 영업현금흐름', f"{h1_2026['영업현금흐름']:.1f}십억원", '2025H1 201.1십억원 대비 감소')
    insight_box('이 탭의 결론',[
        '2024말→2025말에는 공사미수금과 미청구공사가 모두 감소했고, 2025년 연간 영업현금흐름은 5,915억원으로 2024년보다 개선됐습니다.',
        '2026H1에는 미청구공사가 추가로 감소했지만 공사미수금은 다시 증가했습니다.',
        '동시에 2026H1 영업현금흐름은 944억원으로 전년 동기보다 감소했으므로, 매출의 현금화 속도는 계속 확인할 필요가 있습니다.',
        '공사미수금은 사업부별로 완전하게 배분된 공시가 없어 회사 전체 기준으로 분석했습니다.'
    ])

with t5:
    st.subheader('⑤ 최종 진단 — GS건설의 경쟁력을 한 흐름으로 보기')
    st.markdown('''
### 핵심 흐름
**수주 확보 → 매출 전환 → 이익 확보 → 청구·회수 → 현금 창출**
''')
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown('#### ① 일감')
        st.write('2025년 수주잔고는 건축·주택과 신사업/ABED가 핵심 축입니다. 특히 두 사업의 잔고가 2024년보다 증가했습니다.')
    with c2:
        st.markdown('#### ② 실적과 이익')
        st.write('건축·주택 매출 비중은 낮아지는 반면 신사업·플랜트·인프라 매출이 확대됐습니다. 다만 사업별 수익성 변동은 큽니다.')
    with c3:
        st.markdown('#### ③ 현금화')
        st.write('2025년에는 미청구공사·공사미수금 감소와 영업현금흐름 개선이 함께 나타났지만, 2026H1에는 공사미수금 증가와 현금흐름 둔화가 확인됩니다.')

    st.success('''최종 해석: GS건설의 경쟁력은 단순히 많은 수주를 확보하는 데서 끝나지 않습니다. 건축·주택의 큰 수주 기반을 유지하면서 신사업·플랜트·인프라로 매출원을 넓히고, 확보한 일감을 이익과 현금으로 연결하는 능력을 함께 봐야 합니다.''')
    st.info('면접용 한 문장: “공시자료를 활용해 사업별 수주잔고가 매출과 이익으로 전환되는 과정을 분석하고, 마지막으로 미청구공사·공사미수금과 영업현금흐름을 연결해 실적이 실제 현금으로 이어지는지 확인했습니다.”')

st.divider()
with st.expander('출처 및 주의사항'):
    for k,v in SOURCE_NOTES.items():
        st.markdown(f'**{k}**: {v}')
    st.markdown('''
**주의**
- 모든 금액은 화면 가독성을 위해 원 공시의 백만원/십억원 단위를 십억원 기준으로 정리했습니다.
- 2025년부터 사업구분 변경이 있어 장기 비교 시 `신사업 → ABED`, `Green → Plant/Infra`의 연결에 주의해야 합니다.
- 2026H1 미청구공사는 반기보고서 사업부별 계약자산 합계(충당금 차감 전)를 사용했습니다.
- 사업부별 영업현금흐름은 공시되지 않아 추정하지 않았습니다.
''')
