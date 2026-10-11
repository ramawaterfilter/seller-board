"""CON-05 read-only operations validated against Shopify Admin 2026-07."""

PROBE = """
query RciShopifyProbe { shop { id name myshopifyDomain currencyCode ianaTimezone
billingAddress { countryCodeV2 } } currentAppInstallation { accessScopes { handle } } }
"""

PRODUCTS = """
query RciProducts($after: String) { products(first: 100, after: $after) { nodes { id title
status updatedAt } pageInfo { hasNextPage endCursor } } }
"""

VARIANTS = """
query RciVariants($after: String) { productVariants(first: 100, after: $after) { nodes {
id sku title updatedAt product { id } inventoryItem { id } } pageInfo { hasNextPage
endCursor } } }
"""

INVENTORY = """
query RciInventory($after: String) { inventoryItems(first: 100, after: $after) { nodes {
id sku tracked updatedAt } pageInfo { hasNextPage endCursor } } }
"""

LEVELS = """
query RciInventoryLevels($id: ID!, $after: String) { inventoryItem(id: $id) { id
inventoryLevels(first: 100, after: $after) { nodes { id location { id name }
quantities(names: ["available", "on_hand", "committed"]) { name quantity } } pageInfo {
hasNextPage endCursor } } } }
"""

ORDERS = """
query RciOrders($after: String, $query: String!) { orders(first: 50, after: $after, query:
$query, sortKey: CREATED_AT) { nodes { id createdAt updatedAt cancelledAt
displayFinancialStatus displayFulfillmentStatus currentTotalPriceSet { shopMoney { amount
currencyCode } } totalRefundedSet { shopMoney { amount currencyCode } } } pageInfo {
hasNextPage endCursor } } }
"""

LINES = """
query RciOrderLines($id: ID!, $after: String) { order(id: $id) { id lineItems(first: 100,
after: $after) { nodes { id sku quantity variant { id } originalUnitPriceSet { shopMoney {
amount currencyCode } } discountedTotalSet { shopMoney { amount currencyCode } } }
pageInfo { hasNextPage endCursor } } } }
"""
