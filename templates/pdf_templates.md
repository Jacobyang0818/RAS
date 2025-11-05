<style>
@page { size: A4; margin: 24pt 28pt 28pt 28pt; }
body {
  font-family: "Cambria", "PingFang TC", Arial, sans-serif;
  line-height: 1.5;
}
h1 { text-align: center; margin-top: 8pt; margin-bottom: 12pt; font-size: 22pt; }
h2 { margin-top: 16pt; margin-bottom: 6pt; font-size: 14pt; }

.row { display: flex; gap: 10pt; justify-content: space-between; }
.card { flex: 1; text-align: center; }
.card img { width: 100%; height: auto; }
.caption { font-size: 9pt; color: #555; margin-top: 4pt; }
</style>


# Sales Report
<p style="text-align:right; font-size:10pt; color:#666;">Generated on: {{generated_on}}</p>

## A. Charts

<div class="row">
  <div class="card">
    <img src="data:image/png;base64,{{img_client}}" />
    <div class="caption">Sales share by client</div>
  </div>
  <div class="card">
    <img src="data:image/png;base64,{{img_prod}}" />
    <div class="caption">Sales share by product</div>
  </div>
  <div class="card">
    <img src="data:image/png;base64,{{img_id}}" />
    <div class="caption">Sales share by sale_id</div>
  </div>
</div>

<br/>

<div>
  <img src="data:image/png;base64,{{img_line}}" />
  <div class="caption" style="text-align:center;">Daily sales trend</div>
</div>

## B. Summary
- Total revenue: **{{total_rev}}**
- Top client: **{{top_client}}**
- Top product: **{{top_product}}**
