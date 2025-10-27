import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
sys.path.append('..')
from db_connection import (
    get_company_list, 
    get_company_financials,
    get_company_budget_variance,
    get_company_kpis,
    get_company_comments
)

st.title("📈 Company Deep Dive")

# Set dark mode permanently
st._config.set_option('theme.base', 'dark')

with st.sidebar:
    st.header("Filters")
    
    companies_df = get_company_list()
    
    if companies_df is not None and not companies_df.empty:
        company_options = {row['company_name']: row['company_id'] 
                          for _, row in companies_df.iterrows()}
        
        selected_company_name = st.selectbox(
            "Select Company",
            options=list(company_options.keys()),
            index=0
        )
        
        selected_company_id = company_options[selected_company_name]
    else:
        st.error("No companies available")
        st.stop()

if selected_company_id == 'C001':
    
    financials_df = get_company_financials(selected_company_id)
    
    if financials_df is None or financials_df.empty:
        st.error("No financial data available for this company")
        st.stop()
    
    latest_data = financials_df.iloc[-1]
    
    st.subheader(f"{selected_company_name}")
    st.caption(f"Industry: {latest_data['industry']} | Employees: {int(latest_data['employees']) if pd.notna(latest_data['employees']) else 'N/A'}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Latest Revenue",
            f"€{latest_data['revenue']:.1f}M",
            delta=f"{latest_data['revenue_mom_growth_pct']:.1f}% MoM" if pd.notna(latest_data['revenue_mom_growth_pct']) else None
        )
    
    with col2:
        st.metric(
            "Latest EBITDA",
            f"€{latest_data['ebitda']:.1f}M",
            delta=f"{latest_data['ebitda_mom_growth_pct']:.1f}% MoM" if pd.notna(latest_data['ebitda_mom_growth_pct']) else None
        )
    
    with col3:
        st.metric(
            "EBITDA Margin",
            f"{latest_data['ebitda_margin']:.1f}%",
            delta=f"{latest_data['margin_change_bps']:.0f} bps" if pd.notna(latest_data['margin_change_bps']) else None
        )
    
    with col4:
        leverage_value = latest_data['net_leverage_ratio']
        if pd.notna(leverage_value):
            leverage_color = "🟢" if leverage_value < 3.0 else "🟡" if leverage_value < 5.0 else "🔴"
            st.metric(
                "Net Leverage",
                f"{leverage_value:.2f}x",
                delta=leverage_color
            )
        else:
            st.metric("Net Leverage", "N/A")
    
    st.divider()
    
    with st.expander("📊 Financial Metrics Table", expanded=False):
        # Select last 12 months and pivot
        recent_data = financials_df.tail(12).copy()
        
        # Create grouped metrics with blank rows
        metrics_data = {
            'Metric': [
                'Revenue (€M)',
                'Revenue MoM Growth %',
                'Revenue YoY Growth %',
                '',
                'Gross Profit (€M)',
                'Gross Margin %',
                '',
                'EBITDA (€M)',
                'EBITDA Margin %',
                'EBITDA MoM Growth %',
                'EBITDA YoY Growth %',
                '',
                'Cash Conversion %',
                'Net Leverage Ratio'
            ]
        }
        
        # Add each month as a column
        for _, row in recent_data.iterrows():
            month = row['year_month']
            metrics_data[month] = [
                f"{row['revenue']:.2f}" if pd.notna(row['revenue']) else '-',
                f"{row['revenue_mom_growth_pct']:.1f}" if pd.notna(row['revenue_mom_growth_pct']) else '-',
                f"{row['revenue_yoy_growth_pct']:.1f}" if pd.notna(row['revenue_yoy_growth_pct']) else '-',
                '',  # Blank row
                f"{row['gross_profit']:.2f}" if pd.notna(row['gross_profit']) else '-',
                f"{row['gross_margin_pct']:.1f}" if pd.notna(row['gross_margin_pct']) else '-',
                '',  # Blank row
                f"{row['ebitda']:.2f}" if pd.notna(row['ebitda']) else '-',
                f"{row['ebitda_margin']:.1f}" if pd.notna(row['ebitda_margin']) else '-',
                f"{row['ebitda_mom_growth_pct']:.1f}" if pd.notna(row['ebitda_mom_growth_pct']) else '-',
                f"{row['ebitda_yoy_growth_pct']:.1f}" if pd.notna(row['ebitda_yoy_growth_pct']) else '-',
                '',  # Blank row
                f"{row['cash_conversion_pct']:.1f}" if pd.notna(row['cash_conversion_pct']) else '-',
                f"{row['net_leverage_ratio']:.2f}" if pd.notna(row['net_leverage_ratio']) else '-'
            ]
        
        pivot_df = pd.DataFrame(metrics_data)
        
        st.dataframe(
            pivot_df,
            width='stretch',
            hide_index=True
        )
    
    st.subheader("📈 Monthly Trends")
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Revenue & YoY Growth', 'EBITDA & Margin %', 
                       'Gross Profit & Margin %', 'OpEx & % of Revenue'),
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"secondary_y": True}, {"secondary_y": True}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # Chart 1: Revenue + YoY Growth
    fig.add_trace(
        go.Bar(x=financials_df['date'], y=financials_df['revenue'],
              name='Revenue', marker=dict(color='#5DADE2', opacity=0.7),
              hovertemplate='Revenue: €%{y:.2f}M<extra></extra>'),
        row=1, col=1, secondary_y=False
    )
    # Only show labels for quarterly months (Mar, Jun, Sep, Dec)
    text_labels_1 = [f"{val:.1f}%" if pd.notna(val) and pd.to_datetime(date).month in [3, 6, 9, 12] else "" 
                     for date, val in zip(financials_df['date'], financials_df['revenue_yoy_growth_pct'])]
    fig.add_trace(
        go.Scatter(x=financials_df['date'], y=financials_df['revenue_yoy_growth_pct'],
                  name='YoY Growth %', line=dict(color='#67EBF5', width=2),
                  mode='lines+markers+text',
                  text=text_labels_1,
                  textposition='top center', textfont=dict(size=9),
                  hovertemplate='YoY Growth: %{y:.1f}%<extra></extra>'),
        row=1, col=1, secondary_y=True
    )
    
    # Chart 2: EBITDA + Margin
    fig.add_trace(
        go.Bar(x=financials_df['date'], y=financials_df['ebitda'],
              name='EBITDA', marker=dict(color='#5DADE2', opacity=0.7),
              hovertemplate='EBITDA: €%{y:.2f}M<extra></extra>'),
        row=1, col=2, secondary_y=False
    )
    text_labels_2 = [f"{val:.1f}%" if pd.notna(val) and pd.to_datetime(date).month in [3, 6, 9, 12] else "" 
                     for date, val in zip(financials_df['date'], financials_df['ebitda_margin'])]
    fig.add_trace(
        go.Scatter(x=financials_df['date'], y=financials_df['ebitda_margin'],
                  name='Margin %', line=dict(color='#67EBF5', width=2),
                  mode='lines+markers+text',
                  text=text_labels_2,
                  textposition='top center', textfont=dict(size=9),
                  hovertemplate='EBITDA Margin: %{y:.1f}%<extra></extra>'),
        row=1, col=2, secondary_y=True
    )
    
    # Chart 3: Gross Profit + Margin
    fig.add_trace(
        go.Bar(x=financials_df['date'], y=financials_df['gross_profit'],
              name='Gross Profit', marker=dict(color='#5DADE2', opacity=0.7),
              hovertemplate='Gross Profit: €%{y:.2f}M<extra></extra>'),
        row=2, col=1, secondary_y=False
    )
    text_labels_3 = [f"{val:.1f}%" if pd.notna(val) and pd.to_datetime(date).month in [3, 6, 9, 12] else "" 
                     for date, val in zip(financials_df['date'], financials_df['gross_margin_pct'])]
    fig.add_trace(
        go.Scatter(x=financials_df['date'], y=financials_df['gross_margin_pct'],
                  name='GM %', line=dict(color='#67EBF5', width=2),
                  mode='lines+markers+text',
                  text=text_labels_3,
                  textposition='top center', textfont=dict(size=9),
                  hovertemplate='Gross Margin: %{y:.1f}%<extra></extra>'),
        row=2, col=1, secondary_y=True
    )
    
    # Chart 4: OpEx + % of Revenue
    fig.add_trace(
        go.Bar(x=financials_df['date'], y=financials_df['operating_expenses'],
              name='OpEx', marker=dict(color='#5DADE2', opacity=0.7),
              hovertemplate='OpEx: €%{y:.2f}M<extra></extra>'),
        row=2, col=2, secondary_y=False
    )
    text_labels_4 = [f"{val:.1f}%" if pd.notna(val) and pd.to_datetime(date).month in [3, 6, 9, 12] else "" 
                     for date, val in zip(financials_df['date'], financials_df['opex_pct_of_revenue'])]
    fig.add_trace(
        go.Scatter(x=financials_df['date'], y=financials_df['opex_pct_of_revenue'],
                  name='OpEx %', line=dict(color='#67EBF5', width=2),
                  mode='lines+markers+text',
                  text=text_labels_4,
                  textposition='top center', textfont=dict(size=9),
                  hovertemplate='% of Revenue: %{y:.1f}%<extra></extra>'),
        row=2, col=2, secondary_y=True
    )
    
    # Update axes
    fig.update_xaxes(showgrid=False, type='date', tickformat='%b %y')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(211, 211, 211, 0.2)')
    
    # Set y-axis titles
    fig.update_yaxes(title_text="€M", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="%", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="€M", row=1, col=2, secondary_y=False)
    fig.update_yaxes(title_text="%", row=1, col=2, secondary_y=True)
    fig.update_yaxes(title_text="€M", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="%", row=2, col=1, secondary_y=True)
    fig.update_yaxes(title_text="€M", row=2, col=2, secondary_y=False)
    fig.update_yaxes(title_text="%", row=2, col=2, secondary_y=True)
    
    fig.update_layout(
        height=700,
        showlegend=False,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("📊 Budget vs Actual Analysis")
    
    budget_df = get_company_budget_variance(selected_company_id)
    
    if budget_df is not None and not budget_df.empty:
        budget_df_2024 = budget_df[budget_df['year'] == 2024].copy()
        
        if not budget_df_2024.empty:
            latest_ytd = budget_df_2024.iloc[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "YTD Revenue",
                    f"€{latest_ytd['ytd_actual_revenue']:.1f}M",
                    delta=f"{latest_ytd['ytd_variance_revenue_pct']:.1f}% vs Budget"
                )
            
            with col2:
                st.metric(
                    "YTD EBITDA",
                    f"€{latest_ytd['ytd_actual_ebitda']:.1f}M",
                    delta=f"{latest_ytd['ytd_variance_ebitda_pct']:.1f}% vs Budget"
                )
            
            with col3:
                st.metric(
                    "YTD Budget Rev",
                    f"€{latest_ytd['ytd_budget_revenue']:.1f}M"
                )
            
            with col4:
                st.metric(
                    "YTD Budget EBITDA",
                    f"€{latest_ytd['ytd_budget_ebitda']:.1f}M"
                )
            
            fig_budget = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Monthly Revenue: Actual vs Budget', 'Monthly EBITDA: Actual vs Budget'),
                horizontal_spacing=0.15
            )
            
            fig_budget.add_trace(
                go.Bar(x=budget_df_2024['year_month'], y=budget_df_2024['actual_revenue'],
                      name='Actual', marker_color='#1f77b4'),
                row=1, col=1
            )
            fig_budget.add_trace(
                go.Bar(x=budget_df_2024['year_month'], y=budget_df_2024['budget_revenue'],
                      name='Budget', marker_color='lightblue', opacity=0.6),
                row=1, col=1
            )
            
            fig_budget.add_trace(
                go.Bar(x=budget_df_2024['year_month'], y=budget_df_2024['actual_ebitda'],
                      name='Actual', marker_color='#ff7f0e', showlegend=False),
                row=1, col=2
            )
            fig_budget.add_trace(
                go.Bar(x=budget_df_2024['year_month'], y=budget_df_2024['budget_ebitda'],
                      name='Budget', marker_color='lightsalmon', opacity=0.6, showlegend=False),
                row=1, col=2
            )
            
            fig_budget.update_xaxes(type='date', tickformat='%b %y')
            fig_budget.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(211, 211, 211, 0.2)')
            
            fig_budget.update_layout(
                height=400,
                showlegend=True,
                barmode='group',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_budget, use_container_width=True)
            
            with st.expander("📋 Detailed Variance Table"):
                # Create pivoted variance table with months as columns
                variance_data = {
                    'Metric': [
                        'Actual Revenue (€M)',
                        'Budget Revenue (€M)',
                        'Revenue Variance %',
                        '',
                        'Actual EBITDA (€M)',
                        'Budget EBITDA (€M)',
                        'EBITDA Variance %'
                    ]
                }
                
                # Add each month as a column
                for _, row in budget_df_2024.iterrows():
                    month = row['year_month']
                    variance_data[month] = [
                        f"{row['actual_revenue']:.2f}" if pd.notna(row['actual_revenue']) else '-',
                        f"{row['budget_revenue']:.2f}" if pd.notna(row['budget_revenue']) else '-',
                        f"{row['variance_revenue_pct']:.1f}" if pd.notna(row['variance_revenue_pct']) else '-',
                        '',  # Blank row
                        f"{row['actual_ebitda']:.2f}" if pd.notna(row['actual_ebitda']) else '-',
                        f"{row['budget_ebitda']:.2f}" if pd.notna(row['budget_ebitda']) else '-',
                        f"{row['variance_ebitda_pct']:.1f}" if pd.notna(row['variance_ebitda_pct']) else '-'
                    ]
                
                variance_pivot_df = pd.DataFrame(variance_data)
                
                st.dataframe(
                    variance_pivot_df,
                    width='stretch',
                    hide_index=True
                )
    else:
        st.info("No budget data available")
    
    st.divider()
    
    st.subheader("🎯 Key Performance Indicators")
    
    kpis_df = get_company_kpis(selected_company_id)
    
    if kpis_df is not None and not kpis_df.empty:
        kpi_names = ['Homes Passed (000s)', 'ARPU (€ / month)', 'Churn Rate (%)']
        
        col1, col2, col3 = st.columns(3)
        
        for col, kpi_name in zip([col1, col2, col3], kpi_names):
            kpi_data = kpis_df[kpis_df['kpi_name'] == kpi_name].copy()
            
            if not kpi_data.empty:
                with col:
                    with st.container(border=True):
                        latest_kpi = kpi_data.iloc[-1]
                        prev_kpi = kpi_data.iloc[-2] if len(kpi_data) > 1 else None
                        
                        delta_val = None
                        if prev_kpi is not None and pd.notna(latest_kpi['mom_change_pct']):
                            delta_val = f"{latest_kpi['mom_change_pct']:.1f}% MoM"
                        
                        st.metric(
                            label=kpi_name,
                            value=f"{latest_kpi['kpi_value']:.2f}",
                            delta=delta_val
                        )
                        
                        fig_kpi = go.Figure()
                        fig_kpi.add_trace(go.Scatter(
                            x=kpi_data['date'],
                            y=kpi_data['kpi_value'],
                            mode='lines+markers',
                            line=dict(width=2),
                            marker=dict(size=4)
                        ))
                        
                        fig_kpi.update_layout(
                            height=200,
                            margin=dict(l=0, r=0, t=20, b=0),
                            showlegend=False,
                            xaxis=dict(showgrid=False, type='date', tickformat='%b %y'),
                            yaxis=dict(showgrid=True, gridcolor='rgba(211, 211, 211, 0.2)')
                        )
                        
                        st.plotly_chart(fig_kpi, use_container_width=True)
                        
                        if latest_kpi['risk_flag']:
                            st.warning("⚠️ Risk threshold exceeded")
    else:
        st.info("No KPI data available")
    
    st.divider()
    
    st.subheader("💬 Comments")
    
    comments_df = get_company_comments(selected_company_id)
    
    if comments_df is not None and not comments_df.empty:
        for _, comment in comments_df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{comment['author']}** - {comment['role']}")
                
                with col2:
                    st.caption(f"{comment['comment_date']}")
                
                st.write(comment['comment_text'])
    else:
        st.info("No comments available")

else:
    st.info(f"📊 Full analytics currently available for **NordicFiber AB**. Please select that company from the dropdown to view detailed performance metrics, KPIs, and budget analysis.")
    st.write("")
    st.write(f"Selected company: **{selected_company_name}** (ID: {selected_company_id})")
