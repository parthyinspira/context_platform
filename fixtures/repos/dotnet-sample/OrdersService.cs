namespace SampleApp;

// Fixture: reads/writes the sample orders table (lineage: source_orders).
public class OrdersService
{
    public void GetOpenOrders()
    {
        // SELECT * FROM source_orders WHERE order_status = 'open'
    }
}
