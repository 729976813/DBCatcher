kpi_name = ["RealCapacity", "Tps", "Qps", "Queries", "ComUpdate", "ComInsert",
            "InnodbBufferPoolReadRequests", "CpuUseRate", "InnodbRowsDeleted",
            "InnodbRowsInserted", "InnodbRowsUpdated", "InnodbRowsRead", "InnodbDataWritten", "InnodbDataWrites"]

master_slave_properties = [2, 3, 4, 5, 6, 7, 8]
slave_slave_properties = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
theta = [0.7] * len(kpi_name)
