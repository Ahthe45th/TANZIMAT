<database url="{{https://www.notion.so/3422a12a84254ef8a249c28c83b3ebc3}}" inline="false">
The title of this Database is: Archives
This Database owns a single Data source, so its views can only reference the owned Data source. Databases can only own a single Data source.
<ancestor-path>

</ancestor-path>
Here are the Database's Data Sources:
You can use the "view" tool on the URL of any Data Source to see its full schema configuration.
<data-sources>
<data-source url="{{collection://5fe52bbf-b055-497b-a846-1c75f47d3458}}">
The title of this Data Source is: Archives

Here is the database's configurable state:
<data-source-state>
{"name":"Archives","schema":{"Name":{"description":"","name":"Name","type":"title"}},"url":"collection://5fe52bbf-b055-497b-a846-1c75f47d3458"}
</data-source-state>

Here is the SQLite table definition for this data source:
<sqlite-table>
CREATE TABLE IF NOT EXISTS "collection://5fe52bbf-b055-497b-a846-1c75f47d3458" (
	url TEXT UNIQUE,
	"Name" TEXT
)
</sqlite-table>
</data-source>
</data-sources>
Here are the Database's Views:
You can use the "view" tool on the URL of any View to see its full configuration.
<views>
<view url="{{view://3ad55b1f-3388-47b1-82e2-b213b4affa01}}">
{"dataSourceUrl":"{{collection://5fe52bbf-b055-497b-a846-1c75f47d3458}}","name":"Default view","properties":["Name"],"type":"table"}
</view>
</views>
</database>