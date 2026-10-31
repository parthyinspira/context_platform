package com.inspira.sample;

// Fixture: reads/writes the sample orders table (lineage: source_orders).
public class OrdersRepository {
    public void findByCustomer(long customerId) {
        // SELECT * FROM source_orders WHERE customer_id = ?
    }
}
