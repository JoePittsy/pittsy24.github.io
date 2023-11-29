---
headline: "Enhancing Dynamics 365 Forms: In-Line Charts in all shapes and sizes!"
summary: Explore the integration of in-line charts in Dynamics 365 forms to elevate data visualization. This post covers how to embed charts but most importantly, adjusting their size
date: 12/11/2023
outputPath: ./blog/dynamics365/inline-charts.html
tags: 
    - Dynamics365
---

## How to embed a Chart

Many are familiar with displaying charts alongside grids in Dynamics 365, but a lesser-known feature allows you to just show the chart in a form.

Achieving this is straightforward in the new form editor. Simply choose your subgrid and activate the 'Show Chart Only' checkbox. For added flexibility, you can enable the 'Allow users to change chart' option.  

![Show Chart Only - Form Editor](/resources/images/dynamics365/inline-charts/show-chart-only.png "Show Chart Only - Form Editor")

This takes our from from drab to slightly less drab... 
The potential is there but the default chart size somewhat limits its practicality.

![Subgrid to Chart](/resources/images/dynamics365/inline-charts/before-after.png "Subgrid to Chart")

Now, you might wonder, how can we resize this chart for better usability?

## Resizing form embedded charts

Now we have successfully surfaced a chart on our form it's only reasonable for us to want to resize it. Unfortunately this is not as easy as one could hope. 


One might assume that increasing the 'Maximum number of rows' property on the subgrid would do the trick. This was a valid approach back in 2016, and recommended by the [CRM Chart Guy](https://crmchartguy.wordpress.com/2016/01/24/charts-on-forms-or-useraccount-specific-dashboards/). But as of December 2023, this method no longer impacts the chart size, and neither does the 'Use available space' option.


Fortunately, I have discovered a solution: editing the form XML, a method officially [supported ](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/supported-customizations#solution-file) for customization. The crucial step is altering the `rowspan`` property. The most efficient tool I have found for this task is the [Form XML Manager](https://www.xrmtoolbox.com/plugins/ITLec.FormXmlManager/) in XrmToolbox. It enables editing and rapid republishing of the XML, allowing for experimentation with different rowspan values to achieve the desired chart size.

```xml
<cell locklevel="0" id="{6787823b-9029-4777-a933-764e726edf4a}" rowspan="8" colspan="1" auto="true"
    showlabel="true">
    <labels>
        <label description="Home vs Away Total Savings" languagecode="1033" />
    </labels>
    <control indicationOfSubgrid="true" id="Subgrid_new_2"
        classid="{E7A81278-8635-4D9E-8D4D-59480B391C5B}">
        <parameters>
            <RecordsPerPage>250</RecordsPerPage>
            <AutoExpand>Auto</AutoExpand>
            <EnableQuickFind>false</EnableQuickFind>
            <EnableViewPicker>false</EnableViewPicker>
            <EnableChartPicker>true</EnableChartPicker>
            <ChartGridMode>Chart</ChartGridMode>
            <TargetEntityType>tn_visit</TargetEntityType>
            <ViewId>{02AF3A75-BF87-EE11-BE36-6045BDD0EDF1}</ViewId>
            <ViewIds>{A95A8474-2567-4F84-B6B2-A09E9E52575A},{02AF3A75-BF87-EE11-BE36-6045BDD0EDF1}</ViewIds>
            <RelationshipName>tn_SavingsBatch_tn_SavingsBatch_tn_Visit</RelationshipName>
            <VisualizationId>{DE63F41E-C287-EE11-BE36-6045BDD27787}</VisualizationId>
        </parameters>
    </control>
</cell> 
```


Once we adjust the rowspan from 4 to 8, the true potential of charts on forms becomes evident.


![Big In-Line Chart](/resources/images/dynamics365/inline-charts/big-chart.png "Big In-Line Chart")

The real strength of these form-level charts lies in their flexibility: users can change both the data source view and the chart type.

For example, sales teams can greatly benefit from this feature. Embedded charts on forms can track individual or team performance metrics. Imagine a chart displaying monthly sales totals. Users can not only switch views to compare different product lines or regions but also adjust the time frame of the data displayed via the view switcher, whether it's the last 3, 6, 9 months, or any other period. This adaptability transforms forms into dynamic tools for real-time performance tracking.

The key take away is the rowspan property in the XML, with it charts become a viable and valuable addition to your Dynamics365 Forms!