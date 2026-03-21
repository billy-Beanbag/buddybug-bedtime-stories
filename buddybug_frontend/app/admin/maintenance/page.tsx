"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { MaintenanceJobDetail } from "@/components/admin/MaintenanceJobDetail";
import { MaintenanceJobRunner, type MaintenanceJobFormValue } from "@/components/admin/MaintenanceJobRunner";
import { MaintenanceJobTable } from "@/components/admin/MaintenanceJobTable";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { MaintenanceJobRead, MaintenanceJobRunResponse } from "@/lib/types";

export default function AdminMaintenancePage() {
  const { token, isAdmin } = useAuth();
  const [jobs, setJobs] = useState<MaintenanceJobRead[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [selectedJob, setSelectedJob] = useState<MaintenanceJobRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [runningId, setRunningId] = useState<number | null>(null);
  const [cancelingId, setCancelingId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [jobTypeFilter, setJobTypeFilter] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function loadJobs(nextStatus = statusFilter, nextJobType = jobTypeFilter) {
    if (!token) {
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await apiGet<MaintenanceJobRead[]>("/admin/maintenance/jobs", {
        token,
        query: {
          status: nextStatus || undefined,
          job_type: nextJobType || undefined,
          limit: 100,
        },
      });
      setJobs(response);
      if (selectedJobId) {
        const refreshedSelected = response.find((item) => item.id === selectedJobId) || null;
        if (!refreshedSelected) {
          setSelectedJobId(null);
          setSelectedJob(null);
        }
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to load maintenance jobs");
    } finally {
      setLoading(false);
    }
  }

  async function loadJobDetail(jobId: number) {
    if (!token) {
      return;
    }
    try {
      const response = await apiGet<MaintenanceJobRead>(`/admin/maintenance/jobs/${jobId}`, { token });
      setSelectedJob(response);
      setSelectedJobId(response.id);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to load maintenance job detail");
    }
  }

  useEffect(() => {
    if (token) {
      void loadJobs();
    }
  }, [token]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can manage maintenance jobs." />;
  }

  if (loading) {
    return <LoadingState message="Loading maintenance jobs..." />;
  }

  async function handleCreate(payload: MaintenanceJobFormValue) {
    if (!token) {
      return;
    }
    setCreating(true);
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      const created = await apiPost<MaintenanceJobRead>("/admin/maintenance/jobs", payload, { token });
      setStatusMessage(`Created maintenance job #${created.id}.`);
      await loadJobs();
      await loadJobDetail(created.id);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to create maintenance job");
      throw err;
    } finally {
      setCreating(false);
    }
  }

  async function handleRun(job: MaintenanceJobRead) {
    if (!token) {
      return;
    }
    setRunningId(job.id);
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      const response = await apiPost<MaintenanceJobRunResponse>(`/admin/maintenance/jobs/${job.id}/run`, undefined, { token });
      setStatusMessage(
        response.job.status === "succeeded"
          ? `Maintenance job #${job.id} completed successfully.`
          : `Maintenance job #${job.id} finished with status ${response.job.status}.`,
      );
      await loadJobs();
      await loadJobDetail(job.id);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to run maintenance job");
    } finally {
      setRunningId(null);
    }
  }

  async function handleCancel(job: MaintenanceJobRead) {
    if (!token) {
      return;
    }
    setCancelingId(job.id);
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      await apiPost<MaintenanceJobRunResponse>(`/admin/maintenance/jobs/${job.id}/cancel`, undefined, { token });
      setStatusMessage(`Canceled maintenance job #${job.id}.`);
      await loadJobs();
      await loadJobDetail(job.id);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to cancel maintenance job");
    } finally {
      setCancelingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Maintenance jobs</h1>
        <p className="mt-2 text-sm text-slate-600">
          Track bounded backfills, rebuilds, and repair runs so schema evolution and derived-data cleanup stay deliberate and auditable.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            <option value="pending">pending</option>
            <option value="running">running</option>
            <option value="succeeded">succeeded</option>
            <option value="failed">failed</option>
            <option value="canceled">canceled</option>
          </select>
          <select
            value={jobTypeFilter}
            onChange={(event) => setJobTypeFilter(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All job types</option>
            <option value="rebuild_discovery_metadata">rebuild_discovery_metadata</option>
            <option value="rebuild_recommendation_data">rebuild_recommendation_data</option>
            <option value="rebuild_child_profiles">rebuild_child_profiles</option>
            <option value="rebuild_account_health">rebuild_account_health</option>
            <option value="rebuild_reengagement">rebuild_reengagement</option>
            <option value="backfill_content_lane_keys">backfill_content_lane_keys</option>
            <option value="repair_download_packages">repair_download_packages</option>
            <option value="custom">custom</option>
          </select>
          <button
            type="button"
            onClick={() => void loadJobs(statusFilter, jobTypeFilter)}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
          >
            Apply filters
          </button>
        </div>
      </section>

      {statusMessage ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{statusMessage}</div>
      ) : null}
      {errorMessage ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-6">
          {jobs.length ? (
            <MaintenanceJobTable
              jobs={jobs}
              selectedJobId={selectedJobId}
              runningId={runningId}
              cancelingId={cancelingId}
              onSelect={(job) => void loadJobDetail(job.id)}
              onRun={handleRun}
              onCancel={handleCancel}
            />
          ) : (
            <EmptyState title="No maintenance jobs yet" description="Create a bounded rebuild or backfill job to get started." />
          )}
          <MaintenanceJobDetail
            job={selectedJob}
            running={selectedJob ? runningId === selectedJob.id : false}
            canceling={selectedJob ? cancelingId === selectedJob.id : false}
            onRun={handleRun}
            onCancel={handleCancel}
          />
        </div>

        <MaintenanceJobRunner creating={creating} onCreate={handleCreate} />
      </div>
    </div>
  );
}
