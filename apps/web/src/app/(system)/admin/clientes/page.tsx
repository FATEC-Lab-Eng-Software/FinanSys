"use client";

import AdminClientsPanel from "@/components/admin/AdminClientsPanel";
import { withAdminAccess } from "@/components/admin/withAdminAccess";

function AdminClientsPage() {
    return <AdminClientsPanel />;
}

export default withAdminAccess(AdminClientsPage);
