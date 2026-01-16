**Task**: "Migrate production database from PostgreSQL 12 to PostgreSQL 15 with zero downtime"

**Complexity Assessment**:
- Steps: 12 (backup, setup replica, sync, test, cutover, verify, rollback plan, etc.)
- Dependencies: 8 (backup → replica → sync → test → cutover → verify)
- Risks: 6 (data loss, downtime, performance degradation, rollback failure, data corruption, version incompatibility)
- External dependencies: 3 (PostgreSQL 15 server, replication tools, monitoring)
- Technical complexity: High (database migration, replication, zero-downtime cutover)
- Reversibility: Partial (can rollback but with data loss window)

**Complexity Score**: 12*10 + 8*5 + 6*3 + 3*10 + 40 + 10 = **228 points**

**Level**: Very Complex

**Recommendation**: Comprehensive plan required + risk analysis + multiple reviews + dry run

**Plan Required**: YES - This is a critical, high-risk operation that requires detailed planning

**Key Considerations**:
1. **Data Loss Risk**: Any failure could result in data loss
2. **Downtime Risk**: Zero-downtime requirement is challenging
3. **Rollback Complexity**: Must have tested rollback procedure
4. **Version Compatibility**: PostgreSQL 12 → 15 has breaking changes
5. **Performance Impact**: Replication may affect production performance
6. **Testing Requirements**: Must test on staging environment first

**Plan Outline**:

### Phase 1: Preparation (2 days)
1. Backup production database (full backup + WAL archiving)
2. Set up PostgreSQL 15 server (same specs as production)
3. Configure replication (logical replication for zero downtime)
4. Test replication on staging environment
5. Document rollback procedure

### Phase 2: Replication Setup (1 day)
6. Enable logical replication on PostgreSQL 12
7. Create publication on source database
8. Create subscription on PostgreSQL 15
9. Verify replication lag < 1 second
10. Monitor replication for 24 hours

### Phase 3: Testing (1 day)
11. Run read-only queries on PostgreSQL 15
12. Verify data consistency (row counts, checksums)
13. Test application compatibility with PostgreSQL 15
14. Performance testing (query performance, connection pooling)
15. Load testing (simulate production traffic)

### Phase 4: Cutover (4 hours)
16. Schedule maintenance window (low-traffic period)
17. Stop writes to PostgreSQL 12 (read-only mode)
18. Wait for replication to catch up (lag = 0)
19. Verify data consistency one final time
20. Update application connection strings to PostgreSQL 15
21. Enable writes on PostgreSQL 15
22. Monitor for errors (5 minutes)
23. Verify application functionality

### Phase 5: Verification (2 hours)
24. Run smoke tests on all critical features
25. Monitor database performance metrics
26. Check error logs for issues
27. Verify backup jobs are working
28. Update monitoring dashboards

### Phase 6: Cleanup (1 day)
29. Keep PostgreSQL 12 running for 7 days (rollback window)
30. Monitor PostgreSQL 15 for issues
31. After 7 days: decommission PostgreSQL 12
32. Update documentation

**Risks**:
1. **Data Loss** (Critical) - Mitigation: Multiple backups, tested rollback
2. **Extended Downtime** (High) - Mitigation: Dry run, rollback plan
3. **Performance Degradation** (Medium) - Mitigation: Load testing, monitoring
4. **Replication Lag** (Medium) - Mitigation: Monitor lag, optimize queries
5. **Application Incompatibility** (Medium) - Mitigation: Compatibility testing
6. **Rollback Failure** (Critical) - Mitigation: Test rollback procedure

**Success Criteria**:
- Zero data loss
- Downtime < 5 minutes (during cutover)
- All application features working
- Performance equal or better than PostgreSQL 12
- Successful rollback test completed
- 7-day monitoring period with no issues

**Estimated Effort**: 5 days (with 2-person team)

**Recommendation**: This task REQUIRES a comprehensive plan. Do NOT attempt without detailed planning, testing, and approval from stakeholders.
