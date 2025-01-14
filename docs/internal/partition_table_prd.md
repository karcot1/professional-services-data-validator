# Partitioned Tables Design

## Why Partition?

The Data Validation Tool performs row validation by comparing every row in the source database with the corresponding row in the target database. Since the comparison is done in memory, this can create constraints with large tables. One way to address this error is to partition the source and target table into several corresponding partitions. Then, validate the source and target partitions one at a time (either sequentially or in parallel). If the validation is performed in parallel on multiple VMs or containers, this approach has the added benefit of speeding up data validation. This primarily applies to row validation, as column and schema validations don't bring each row into memory.

## How to partition?

Data Validation Tool matches rows based on the specified primary key(s). If we split up the table into small enough partitions, then each partition can be validated without running into memory errors. This can be depicted pictorially as shown below:
![Alt text](./partition_picture.png?raw=true "Title")
Here, both tables are sorted by primary key(s). The blue line denotes the first row of each partition. With tables partitioned as shown, the complete tables can be row validated by concatenating the results of validating each partition source table against the corresponding partition of the target table.

### What filter clause to use?

Data Validation Tool has an option in the row validation command for a `--filters` parameter which allows a WHERE statement to be applied to the query used to validate. This parameter can be used to partition the table. The filter clauses are:

1. For the first partition, it is every row with primary key(s) value smaller than the first row of second partition
1. For the last partition, it is every row with primary key(s) value larger than or equal to the the first row of last partition.
1. For all other partitions, it is every row with primary key(s) value larger than or equal to to the first row of the current partition *AND* with primary key(s) values less than the first row of the next partition.

### How to calculate the first row of each partition?

The first version of generate partitions used the NTILE function. Unfortunately, Teradata does not have the NTILE function. Almost every database has a ROWNUMBER() function which assigns a row number to each row. This function can be used to generate equal sized partitions. Let the rows be numbered from 0 to count where count is the number of rows in the table. Let us assume we want to partition the table in n equal sized partitions. The partition number associated with a row is its _ceiling(rownumber * n / count)_. We specifically only need to identify first element of the partition. The first element of a partition is the one whose remainder of _(rownumber * n) % count_ is _> 0 and  \<= n_.  The following SQL statement gets the value of the primary key(s) for the first row of each partition:

```sql
SELECT
            primary_key_1,
            primary_key_2,
            ....
            row_num
                FROM   (
                    SELECT   primary_key_1,
                        primary_key_2,
                        ....,
                        rownumber OVER (ORDER BY primary_key_1, primary_key_2, .... ) row_num
                        FROM     <database_table>)
            WHERE ((row_num * n) % count > 0) and ((row_num *n) % count <=n)
ORDER BY row_num ASC;
```

### How to generate the WHERE clauses

Once we have the first row of each partition, we have to generate the where clauses for each partition in the source and target tables. We generate the Ibis table expression including the provided filter clause and the additional filter clause from the first rows we have calculated. We can then have _ibis_ `to_sql` convert the table expression into plain text, extract the where clause and use that. _ibis_ depends on _sqlalchemy_, which has a bug in that it does not support rendering date and timestamps by `to_sql` for versions of _sqlalchemy_ prior to 2.0. Until we migrate to using _sqlalchemy_ 2.0, we may not be able to support dates and timestamps as a primary key column.

## Future Work

### Recommending partition numbers

The `generate-table-partitions` command requires that the user provide the number of partitions to create. Currently, the user needs to decide the partition number by trial and error based on the compute resources available. Python's `psutil` package has a function [virtual_memory()](https://psutil.readthedocs.io/en/latest/#psutil.virtual_memory) which tells us the total and available memory. `generate-table-partitions` is provided with all the parameters used in `validate row`, and the memory grows linearly to the number of rows being validated. `generate-table-partitions` can bring say 10,000 rows into memory as though performing a row validation. Using the virtual_memory() function in `psutil`, `generate-table-partitions` can estimate the number of rows that will fit in memory for row validation. Since we can calculate the total number of rows, we can estimate the number of partitions needed. This may need some experimentation, as we may need to allow for memory usage by other functions/objects in the Data Validation Tool.
