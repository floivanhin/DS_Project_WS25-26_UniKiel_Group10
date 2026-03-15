# AUTO GENERATED FILE - DO NOT EDIT

import typing  # noqa: F401
from typing_extensions import TypedDict, NotRequired, Literal # noqa: F401
from dash.development.base_component import Component, _explicitize_args

ComponentSingleType = typing.Union[str, int, float, Component, None]
ComponentType = typing.Union[
    ComponentSingleType,
    typing.Sequence[ComponentSingleType],
]

NumberType = typing.Union[
    typing.SupportsFloat, typing.SupportsInt, typing.SupportsComplex
]


class AgGrid(Component):
    """An AgGrid component.
Dash interface to AG Grid, a powerful tabular data component.

Keyword arguments:

- id (string; optional):
    The ID used to identify this component in Dash callbacks.

- cellClicked (dict; optional):
    Cell is clicked.

    `cellClicked` is a dict with keys:

    - value (boolean | number | string | dict | list; optional):
        value of the clicked cell.

    - colId (boolean | number | string | dict | list; optional):
        column where the cell was clicked.

    - rowIndex (number; optional):
        rowIndex, typically a row number.

    - rowId (boolean | number | string | dict | list; optional):
        Row Id from the grid, this could be a number automatically, or
        set via getRowId.

    - timestamp (boolean | number | string | dict | list; optional):
        timestamp of last action.

- cellDoubleClicked (dict; optional):
    Cell is double clicked.

    `cellDoubleClicked` is a dict with keys:

    - value (boolean | number | string | dict | list; optional):
        value of the double-clicked cell.

    - colId (boolean | number | string | dict | list; optional):
        column where the cell was double-clicked.

    - rowIndex (number; optional):
        rowIndex, typically a row number.

    - rowId (boolean | number | string | dict | list; optional):
        Row Id from the grid, this could be a number automatically, or
        set via getRowId.

    - timestamp (boolean | number | string | dict | list; optional):
        timestamp of last action.

- cellRendererData (dict; optional):
    Special prop to allow feedback from cell renderer to the grid.

    `cellRendererData` is a dict with keys:

    - value (boolean | number | string | dict | list; optional):
        Value set from the function.

    - colId (string; optional):
        Column ID from where the event was fired.

    - rowIndex (number; optional):
        Row Index from the grid, this is associated with the row
        count.

    - rowId (boolean | number | string | dict | list; optional):
        Row Id from the grid, this could be a number automatically, or
        set via getRowId.

    - timestamp (boolean | number | string | dict | list; optional):
        Timestamp of when the event was fired.

- cellValueChanged (list of dicts; optional):
    Value has changed after editing.

    `cellValueChanged` is a list of dicts with keys:

    - rowIndex (number; optional):
        rowIndex, typically a row number.

    - rowId (boolean | number | string | dict | list; optional):
        Row Id from the grid, this could be a number automatically, or
        set via getRowId.

    - data (dict; optional):
        data, data object from the row.

    - oldValue (boolean | number | string | dict | list; optional):
        old value of the cell.

    - newValue (boolean | number | string | dict | list; optional):
        new value of the cell.

    - colId (boolean | number | string | dict | list; optional):
        column where the cell was changed.

    - timestamp (boolean | number | string | dict | list; optional):
        Timestamp of when the event was fired.

- className (string; default ''):
    The class for the ag-grid.  Can specify the ag-grid theme here.

- columnDefs (list of dicts; optional):
    Array of Column Definitions.

- columnSize (a value equal to: 'sizeToFit', 'autoSize', 'responsiveSizeToFit', null; optional):
    Size the columns autoSize changes the column sizes to fit the
    column's content, sizeToFit changes the column sizes to fit the
    width of the table responsiveSizeToFit changes the column sizes to
    fit the width of the table and also resizing upon grid or column
    changes and None bypasses the altering of the column widths.

- columnSizeOptions (dict; optional):
    Options to customize the columnSize operation. autoSize calls
    either autoSizeColumns or autoSizeAllColumns, see:
    https://www.ag-grid.com/react-data-grid/column-sizing/#autosize-column-api,
    and sizeToFit and responsiveSizeToFit call sizeColumnsToFit, see:
    https://www.ag-grid.com/react-data-grid/column-sizing/#size-columns-to-fit.

    `columnSizeOptions` is a dict with keys:

    - columnLimits (list of dicts; optional):
        for (responsive)sizeToFit: per-column minimum and maximum
        width, in pixels.

        `columnLimits` is a list of dicts with keys:

        - key (string; optional)

        - minWidth (number; optional)

        - maxWidth (number; optional)

    - defaultMinWidth (number; optional):
        for (responsive)sizeToFit: default minimum width, in pixels,
        if not overridden by columnLimits.

    - defaultMaxWidth (number; optional):
        for (responsive)sizeToFit: default maximum width, in pixels,
        if not overridden by columnLimits.

    - keys (list of strings; optional):
        for autoSize: list of column keys to autosize. If omitted, all
        columns will be autosized.

    - skipHeader (boolean; optional):
        for autoSize: If skipHeader=True, the header won't be included
        when calculating the column widths. default: False.

- columnState (list; optional):
    Current state of the columns.

- csvExportParams (dict; optional):
    Object with properties to pass to the exportDataAsCsv() method.

    `csvExportParams` is a dict with keys:

    - columnSeparator (string; optional):
        Delimiter to insert between cell values.

    - suppressQuotes (boolean; optional):
        Pass True to insert the value into the CSV file without
        escaping. In this case it is your responsibility to ensure
        that no cells contain the columnSeparator character.

    - prependContent (string; optional):
        Content to put at the top of the file export. A 2D array of
        CsvCell objects.

    - appendContent (string; optional):
        Content to put at the bottom of the file export.

    - allColumns (boolean; optional):
        If True, all columns will be exported in the order they appear
        in the columnDefs.

    - columnKeys (list of strings; optional):
        Provide a list (an array) of column keys or Column objects if
        you want to export specific columns.

    - fileName (string; optional):
        String to use as the file name.

    - onlySelected (boolean; optional):
        Export only selected rows.

    - onlySelectedAllPages (boolean; optional):
        Only export selected rows including other pages (only makes
        sense when using pagination).

    - skipColumnGroupHeaders (boolean; optional):
        Set to True to skip include header column groups.

    - skipColumnHeaders (boolean; optional):
        Set to True if you don't want to export column headers.

    - skipRowGroups (boolean; optional):
        Set to True to skip row group headers if grouping rows. Only
        relevant when grouping rows.

    - skipPinnedTop (boolean; optional):
        Set to True to suppress exporting rows pinned to the top of
        the grid.

    - skipPinnedBottom (boolean; optional):
        Set to True to suppress exporting rows pinned to the bottom of
        the grid.

- dangerously_allow_code (boolean; default False):
    Allow strings containing JavaScript code or HTML in certain props.
    If your app stores Dash layouts for later retrieval this is
    dangerous because it can lead to cross-site-scripting attacks.

- dashGridOptions (dict; optional):
    Other ag-grid options.

- dashRenderType (string; optional):
    dashRenderType to determine why grid is rendering.

- defaultColDef (dict; optional):
    A default column definition.

- deleteSelectedRows (boolean; optional):
    If True, the internal method deleteSelectedRows() will be called.

- deselectAll (boolean; default False):
    If True, the internal method deselectAll() will be called.

- detailCellRendererParams (dict; optional):
    Specifies the params to be used by the default detail Cell
    Renderer. See Detail Grids.

    `detailCellRendererParams` is a dict with keys:

    - detailGridOptions (boolean | number | string | dict | list; optional):
        Grid options for detail grid in master-detail view.

    - detailColName (string; optional):
        Column name where detail grid data is located in main dataset,
        for master-detail view.

    - suppressCallback (boolean; optional):
        Default: True. If True, suppresses the Dash callback in favor
        of using the data embedded in rowData at the given
        detailColName.

- enableEnterpriseModules (boolean; default False):
    If True, enable ag-grid Enterprise modules. Recommended to use
    with licenseKey.

- eventData (dict; optional):
    Object of Event Data from the grid, based upon when a user
    triggered an event with an event listener.

    `eventData` is a dict with keys:

    - data (boolean | number | string | dict | list; optional):
        Data that the developers passes back.

    - timestamp (boolean | number | string | dict | list; optional):
        Timestamp of when the event was fired.

- eventListeners (dict with strings as keys and values of type list; optional):
    Object of Eventlisteners to add upon grid ready. These listeners
    are only added upon grid ready. To add or remove an event listener
    after this point, please utilize the `getApi` or `getApiAsync`
    methods.

- exportDataAsCsv (boolean; default False):
    If True, the internal method exportDataAsCsv() will be called.

- filterModel (dict; optional):
    If filtering client-side rowModel, what the filter model is.
    Passing a model back to this prop will apply it to the grid.

- getDetailRequest (dict; optional):
    Request from Dash AgGrid when suppressCallback is disabled and a
    user opens a row with a detail grid.

    `getDetailRequest` is a dict with keys:

    - data (boolean | number | string | dict | list; optional):
        Details about the row that was opened.

    - requestTime (boolean | number | string | dict | list; optional):
        Datetime representing when the grid was requested.

- getDetailResponse (list of dicts; optional):
    RowData to populate the detail grid when callbacks are used to
    populate.

- getRowId (string; optional):
    This is required for change detection in rowData.

- getRowStyle (dict; optional):
    Object used to perform the row styling. See AG-Grid Row Style.

    `getRowStyle` is a dict with keys:

    - styleConditions (list of dicts; optional)

        `styleConditions` is a list of dicts with keys:

        - condition (string; required)

        - style (dict; required)

    - defaultStyle (dict; optional)

- getRowsRequest (dict; optional):
    Infinite Scroll, Datasource interface See
    https://www.ag-grid.com/react-grid/infinite-scrolling/#datasource-interface.

    `getRowsRequest` is a dict with keys:

    - startRow (number; optional):
        The first row index to get.

    - endRow (number; optional):
        The first row index to NOT get.

    - sortModel (list of dicts; optional):
        If sorting, what the sort model is.

    - filterModel (dict; optional):
        If filtering, what the filter model is.

    - context (boolean | number | string | dict | list; optional):
        The grid context object.

    - successCallback (optional):
        Callback to call when the request is successful.

    - failCallback (optional):
        Callback to call when the request fails.

- getRowsResponse (dict; optional):
    Serverside model data response object. See
    https://www.ag-grid.com/react-grid/server-side-model-datasource/.

    `getRowsResponse` is a dict with keys:

    - rowData (list of dicts; optional):
        Data retreived from the server.

    - rowCount (number; optional):
        Current row count, if known.

    - storeInfo (boolean | number | string | dict | list; optional):
        Any extra info for the grid to associate with this load.

- licenseKey (string; optional):
    License key for ag-grid enterprise. If using Enterprise modules,
    enableEnterpriseModules must also be True.

- masterDetail (boolean; optional):
    Used to enable Master Detail. See Enabling Master Detail. Default
    Value: False.

- paginationGoTo (a value equal to: 'first', 'last', 'next', 'previous', null | number; optional):
    If in pagination mode, this will navigate to: ['next', 'previous',
    'last', 'first', number]
    https://www.ag-grid.com/react-data-grid/grid-api/#reference-pagination.

- paginationInfo (dict; optional):
    If in pagination mode, this will be populated with info from the
    pagination API:
    https://www.ag-grid.com/react-data-grid/grid-api/#reference-pagination.

    `paginationInfo` is a dict with keys:

    - isLastPageFound (boolean; optional)

    - pageSize (number; optional)

    - currentPage (number; optional)

    - totalPages (number; optional)

    - rowCount (number; optional)

- persisted_props (list of strings; default ['selectedRows']):
    Properties whose user interactions will persist after refreshing
    the component or the page.

- persistence (boolean | string | number; optional):
    Used to allow user interactions in this component to be persisted
    when the component - or the page - is refreshed. If `persisted` is
    truthy and hasn't changed from its previous value, a `value` that
    the user has changed while using the app will keep that change, as
    long as the new `value` also matches what was given originally.
    Used in conjunction with `persistence_type`.

- persistence_type (a value equal to: 'local', 'session', 'memory'; default 'local'):
    Where persisted user changes will be stored: memory: only kept in
    memory, reset on page refresh. local: window.localStorage, data is
    kept after the browser quit. session: window.sessionStorage, data
    is cleared once the browser quit.

- resetColumnState (boolean; default False):
    If True, the internal method resetColumnState() will be called.

- rowClass (string; optional):
    The class to give a particular row. See Row Class.

- rowClassRules (dict; optional):
    Rules which can be applied to include certain CSS classes. See Row
    Class Rules.

- rowData (list of dicts; optional):
    (Client-Side Row Model only) Set the data to be displayed as rows
    in the grid.

- rowModelType (a value equal to: 'clientSide', 'infinite', 'viewport', 'serverSide'; default 'clientSide'):
    Sets the Row Model type. Default Value: 'clientSide'.

- rowStyle (dict; optional):
    The style to give a particular row. See Row Style.

- rowTransaction (dict; optional):
    If True, the internal method rowTransaction() will be used, if
    async provided as False, applyTransaction() will be called, else
    applyTransactionAsync().

    `rowTransaction` is a dict with keys:

    - async (boolean; optional)

    - add (list; optional)

    - update (list; optional)

    - remove (list; optional)

    - addIndex (number; optional)

- scrollTo (dict; optional):
    Scrolls to a specific position.

    `scrollTo` is a dict with keys:

    - rowIndex (number; optional):
        rowIndex, typically a row number.

    - rowId (string; optional):
        Id of the row to scroll to.

    - data (dict; optional):
        Data of the row to scroll to.

    - rowPosition (a value equal to: 'top', 'bottom', 'middle'; optional):
        Position of the row in the grid after scrolling. Default
        `top`.

    - column (string; optional):
        Column to scroll to, must be equal to one `field` in
        `columnDefs`.

    - columnPosition (a value equal to: 'auto', 'start', 'middle', 'end'; optional):
        Position of the column in the grid after scrolling. Default
        `auto`.

- selectAll (dict; default False):
    Set to True to cause all rows to be selected, Or pass an object of
    options for which rows to select. Currently supports `filtered`,
    set to True to only select filtered rows.

    `selectAll` is a boolean | dict with keys:

    - filtered (boolean; optional)

- selectedRows (list of dicts; optional):
    The actively selected rows from the grid (may include filtered
    rows) Can take one of three forms: (1) an array of row objects -
    if you have defined `getRowId`, you only need the fields it uses.
    (2) an object containing `function` with a function string - see:
    https://www.ag-grid.com/react-data-grid/row-selection/#example-using-foreachnode
    (selectAllAmerican function) (3) an object containing `ids` with a
    list of row IDs.

    `selectedRows` is a list of dicts | dict with keys:

    - function (string; required)

      Or dict with keys:

    - ids (list of strings; required)

- suppressDragLeaveHidesColumns (boolean; default True):
    If True, when you drag a column out of the grid (e.g. to the group
    zone) the column is not hidden.

- updateColumnState (boolean; default False):
    If True, the internal method updateColumnState() will be called.

- virtualRowData (list of dicts; optional):
    The rowData in the grid after inline filters are applied."""
    _children_props: typing.List[str] = []
    _base_nodes = ['children']
    _namespace = 'dash_ag_grid'
    _type = 'AgGrid'
    SelectAll = TypedDict(
        "SelectAll",
            {
            "filtered": NotRequired[bool]
        }
    )

    RowTransaction = TypedDict(
        "RowTransaction",
            {
            "async": NotRequired[bool],
            "add": NotRequired[typing.Sequence],
            "update": NotRequired[typing.Sequence],
            "remove": NotRequired[typing.Sequence],
            "addIndex": NotRequired[NumberType]
        }
    )

    CsvExportParams = TypedDict(
        "CsvExportParams",
            {
            "columnSeparator": NotRequired[str],
            "suppressQuotes": NotRequired[bool],
            "prependContent": NotRequired[str],
            "appendContent": NotRequired[str],
            "allColumns": NotRequired[bool],
            "columnKeys": NotRequired[typing.Sequence[str]],
            "fileName": NotRequired[str],
            "onlySelected": NotRequired[bool],
            "onlySelectedAllPages": NotRequired[bool],
            "skipColumnGroupHeaders": NotRequired[bool],
            "skipColumnHeaders": NotRequired[bool],
            "skipRowGroups": NotRequired[bool],
            "skipPinnedTop": NotRequired[bool],
            "skipPinnedBottom": NotRequired[bool]
        }
    )

    ColumnSizeOptionsColumnLimits = TypedDict(
        "ColumnSizeOptionsColumnLimits",
            {
            "key": NotRequired[str],
            "minWidth": NotRequired[NumberType],
            "maxWidth": NotRequired[NumberType]
        }
    )

    ColumnSizeOptions = TypedDict(
        "ColumnSizeOptions",
            {
            "columnLimits": NotRequired[typing.Sequence["ColumnSizeOptionsColumnLimits"]],
            "defaultMinWidth": NotRequired[NumberType],
            "defaultMaxWidth": NotRequired[NumberType],
            "keys": NotRequired[typing.Sequence[str]],
            "skipHeader": NotRequired[bool]
        }
    )

    GetRowStyleStyleConditions = TypedDict(
        "GetRowStyleStyleConditions",
            {
            "condition": str,
            "style": dict
        }
    )

    GetRowStyle = TypedDict(
        "GetRowStyle",
            {
            "styleConditions": NotRequired[typing.Sequence["GetRowStyleStyleConditions"]],
            "defaultStyle": NotRequired[dict]
        }
    )

    GetRowsRequest = TypedDict(
        "GetRowsRequest",
            {
            "startRow": NotRequired[NumberType],
            "endRow": NotRequired[NumberType],
            "sortModel": NotRequired[typing.Sequence[dict]],
            "filterModel": NotRequired[dict],
            "context": NotRequired[typing.Any],
            "successCallback": NotRequired[typing.Any],
            "failCallback": NotRequired[typing.Any]
        }
    )

    PaginationInfo = TypedDict(
        "PaginationInfo",
            {
            "isLastPageFound": NotRequired[bool],
            "pageSize": NotRequired[NumberType],
            "currentPage": NotRequired[NumberType],
            "totalPages": NotRequired[NumberType],
            "rowCount": NotRequired[NumberType]
        }
    )

    GetDetailRequest = TypedDict(
        "GetDetailRequest",
            {
            "data": NotRequired[typing.Any],
            "requestTime": NotRequired[typing.Any]
        }
    )

    CellRendererData = TypedDict(
        "CellRendererData",
            {
            "value": NotRequired[typing.Any],
            "colId": NotRequired[str],
            "rowIndex": NotRequired[NumberType],
            "rowId": NotRequired[typing.Any],
            "timestamp": NotRequired[typing.Any]
        }
    )

    GetRowsResponse = TypedDict(
        "GetRowsResponse",
            {
            "rowData": NotRequired[typing.Sequence[dict]],
            "rowCount": NotRequired[NumberType],
            "storeInfo": NotRequired[typing.Any]
        }
    )

    ScrollTo = TypedDict(
        "ScrollTo",
            {
            "rowIndex": NotRequired[NumberType],
            "rowId": NotRequired[str],
            "data": NotRequired[dict],
            "rowPosition": NotRequired[Literal["top", "bottom", "middle"]],
            "column": NotRequired[str],
            "columnPosition": NotRequired[Literal["auto", "start", "middle", "end"]]
        }
    )

    EventData = TypedDict(
        "EventData",
            {
            "data": NotRequired[typing.Any],
            "timestamp": NotRequired[typing.Any]
        }
    )

    DetailCellRendererParams = TypedDict(
        "DetailCellRendererParams",
            {
            "detailGridOptions": NotRequired[typing.Any],
            "detailColName": NotRequired[str],
            "suppressCallback": NotRequired[bool]
        }
    )

    CellClicked = TypedDict(
        "CellClicked",
            {
            "value": NotRequired[typing.Any],
            "colId": NotRequired[typing.Any],
            "rowIndex": NotRequired[NumberType],
            "rowId": NotRequired[typing.Any],
            "timestamp": NotRequired[typing.Any]
        }
    )

    CellDoubleClicked = TypedDict(
        "CellDoubleClicked",
            {
            "value": NotRequired[typing.Any],
            "colId": NotRequired[typing.Any],
            "rowIndex": NotRequired[NumberType],
            "rowId": NotRequired[typing.Any],
            "timestamp": NotRequired[typing.Any]
        }
    )

    SelectedRows = TypedDict(
        "SelectedRows",
            {
            "ids": typing.Sequence[str]
        }
    )

    CellValueChanged = TypedDict(
        "CellValueChanged",
            {
            "rowIndex": NotRequired[NumberType],
            "rowId": NotRequired[typing.Any],
            "data": NotRequired[dict],
            "oldValue": NotRequired[typing.Any],
            "newValue": NotRequired[typing.Any],
            "colId": NotRequired[typing.Any],
            "timestamp": NotRequired[typing.Any]
        }
    )


    def __init__(
        self,
        id: typing.Optional[typing.Union[str, dict]] = None,
        style: typing.Optional[typing.Any] = None,
        className: typing.Optional[str] = None,
        persistence: typing.Optional[typing.Union[bool, str, NumberType]] = None,
        persisted_props: typing.Optional[typing.Sequence[str]] = None,
        persistence_type: typing.Optional[Literal["local", "session", "memory"]] = None,
        dangerously_allow_code: typing.Optional[bool] = None,
        resetColumnState: typing.Optional[bool] = None,
        exportDataAsCsv: typing.Optional[bool] = None,
        selectAll: typing.Optional[typing.Union[bool, "SelectAll"]] = None,
        deselectAll: typing.Optional[bool] = None,
        updateColumnState: typing.Optional[bool] = None,
        deleteSelectedRows: typing.Optional[bool] = None,
        rowTransaction: typing.Optional["RowTransaction"] = None,
        getRowId: typing.Optional[str] = None,
        columnState: typing.Optional[typing.Sequence] = None,
        csvExportParams: typing.Optional["CsvExportParams"] = None,
        columnSize: typing.Optional[Literal["sizeToFit", "autoSize", "responsiveSizeToFit", None]] = None,
        columnSizeOptions: typing.Optional["ColumnSizeOptions"] = None,
        getRowStyle: typing.Optional["GetRowStyle"] = None,
        getRowsRequest: typing.Optional["GetRowsRequest"] = None,
        paginationInfo: typing.Optional["PaginationInfo"] = None,
        paginationGoTo: typing.Optional[typing.Union[Literal["first", "last", "next", "previous", None], NumberType]] = None,
        filterModel: typing.Optional[dict] = None,
        getDetailRequest: typing.Optional["GetDetailRequest"] = None,
        getDetailResponse: typing.Optional[typing.Sequence[dict]] = None,
        cellRendererData: typing.Optional["CellRendererData"] = None,
        getRowsResponse: typing.Optional["GetRowsResponse"] = None,
        licenseKey: typing.Optional[str] = None,
        enableEnterpriseModules: typing.Optional[bool] = None,
        virtualRowData: typing.Optional[typing.Sequence[dict]] = None,
        scrollTo: typing.Optional["ScrollTo"] = None,
        eventListeners: typing.Optional[typing.Dict[typing.Union[str, float, int], typing.Sequence]] = None,
        eventData: typing.Optional["EventData"] = None,
        columnDefs: typing.Optional[typing.Sequence[dict]] = None,
        defaultColDef: typing.Optional[dict] = None,
        rowModelType: typing.Optional[Literal["clientSide", "infinite", "viewport", "serverSide"]] = None,
        rowData: typing.Optional[typing.Sequence[dict]] = None,
        masterDetail: typing.Optional[bool] = None,
        detailCellRendererParams: typing.Optional["DetailCellRendererParams"] = None,
        rowStyle: typing.Optional[dict] = None,
        rowClass: typing.Optional[str] = None,
        rowClassRules: typing.Optional[dict] = None,
        suppressDragLeaveHidesColumns: typing.Optional[bool] = None,
        cellClicked: typing.Optional["CellClicked"] = None,
        cellDoubleClicked: typing.Optional["CellDoubleClicked"] = None,
        selectedRows: typing.Optional[typing.Union[typing.Sequence[dict], "SelectedRows"]] = None,
        cellValueChanged: typing.Optional[typing.Sequence["CellValueChanged"]] = None,
        dashGridOptions: typing.Optional[dict] = None,
        dashRenderType: typing.Optional[str] = None,
        **kwargs
    ):
        self._prop_names = ['id', 'cellClicked', 'cellDoubleClicked', 'cellRendererData', 'cellValueChanged', 'className', 'columnDefs', 'columnSize', 'columnSizeOptions', 'columnState', 'csvExportParams', 'dangerously_allow_code', 'dashGridOptions', 'dashRenderType', 'defaultColDef', 'deleteSelectedRows', 'deselectAll', 'detailCellRendererParams', 'enableEnterpriseModules', 'eventData', 'eventListeners', 'exportDataAsCsv', 'filterModel', 'getDetailRequest', 'getDetailResponse', 'getRowId', 'getRowStyle', 'getRowsRequest', 'getRowsResponse', 'licenseKey', 'masterDetail', 'paginationGoTo', 'paginationInfo', 'persisted_props', 'persistence', 'persistence_type', 'resetColumnState', 'rowClass', 'rowClassRules', 'rowData', 'rowModelType', 'rowStyle', 'rowTransaction', 'scrollTo', 'selectAll', 'selectedRows', 'style', 'suppressDragLeaveHidesColumns', 'updateColumnState', 'virtualRowData']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'cellClicked', 'cellDoubleClicked', 'cellRendererData', 'cellValueChanged', 'className', 'columnDefs', 'columnSize', 'columnSizeOptions', 'columnState', 'csvExportParams', 'dangerously_allow_code', 'dashGridOptions', 'dashRenderType', 'defaultColDef', 'deleteSelectedRows', 'deselectAll', 'detailCellRendererParams', 'enableEnterpriseModules', 'eventData', 'eventListeners', 'exportDataAsCsv', 'filterModel', 'getDetailRequest', 'getDetailResponse', 'getRowId', 'getRowStyle', 'getRowsRequest', 'getRowsResponse', 'licenseKey', 'masterDetail', 'paginationGoTo', 'paginationInfo', 'persisted_props', 'persistence', 'persistence_type', 'resetColumnState', 'rowClass', 'rowClassRules', 'rowData', 'rowModelType', 'rowStyle', 'rowTransaction', 'scrollTo', 'selectAll', 'selectedRows', 'style', 'suppressDragLeaveHidesColumns', 'updateColumnState', 'virtualRowData']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        super(AgGrid, self).__init__(**args)

setattr(AgGrid, "__init__", _explicitize_args(AgGrid.__init__))
