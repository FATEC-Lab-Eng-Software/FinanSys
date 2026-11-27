"use client";

import SystemOverview from "@/components/admin/SystemOverview";
import { withAdminAccess } from "@/components/admin/withAdminAccess";

function AdminOverviewPage() {
    return <SystemOverview />;
}

export default withAdminAccess(AdminOverviewPage);
