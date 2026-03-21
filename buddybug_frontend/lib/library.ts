import { apiDelete, apiGet, apiPatch, apiPost } from "@/lib/api";
import { fetchOfflinePackagePayload, saveOfflineBookPackage } from "@/lib/offline-storage";
import type {
  BookDownloadPackageRead,
  OfflineBookPackageRecord,
  ReaderDownloadAccessResponse,
  SavedLibraryResponse,
  UserLibraryItemRead,
} from "@/lib/types";

interface LibraryContextOptions {
  token: string;
  childProfileId?: number | null;
}

export function fetchSavedLibrary(options: LibraryContextOptions & { status?: string; savedForOffline?: boolean }) {
  return apiGet<SavedLibraryResponse>("/library/me", {
    token: options.token,
    query: {
      child_profile_id: options.childProfileId ?? undefined,
      status: options.status,
      saved_for_offline: options.savedForOffline,
    },
  });
}

export function saveBook(
  bookId: number,
  options: LibraryContextOptions & { savedForOffline?: boolean },
) {
  return apiPost<UserLibraryItemRead>(
    "/library/me",
    {
      book_id: bookId,
      child_profile_id: options.childProfileId ?? null,
      saved_for_offline: options.savedForOffline ?? false,
    },
    { token: options.token },
  );
}

export function updateLibraryItem(
  bookId: number,
  payload: {
    status?: string;
    saved_for_offline?: boolean;
    last_opened_at?: string;
    downloaded_at?: string;
  },
  options: LibraryContextOptions,
) {
  return apiPatch<UserLibraryItemRead>(`/library/me/books/${bookId}`, payload, {
    token: options.token,
    query: { child_profile_id: options.childProfileId ?? undefined },
  });
}

export function archiveLibraryItem(bookId: number, options: LibraryContextOptions) {
  return apiPost<UserLibraryItemRead>(`/library/me/books/${bookId}/archive`, undefined, {
    token: options.token,
    query: { child_profile_id: options.childProfileId ?? undefined },
  });
}

export function removeLibraryItem(bookId: number, options: LibraryContextOptions) {
  return apiDelete<UserLibraryItemRead>(`/library/me/books/${bookId}`, {
    token: options.token,
    query: { child_profile_id: options.childProfileId ?? undefined },
  });
}

export function markLibraryBookOpened(bookId: number, options: LibraryContextOptions) {
  return apiPost<UserLibraryItemRead | null>(`/library/me/books/${bookId}/opened`, undefined, {
    token: options.token,
    query: { child_profile_id: options.childProfileId ?? undefined },
  });
}

export function fetchDownloadAccess(
  bookId: number,
  options: LibraryContextOptions & { language?: string },
) {
  return apiGet<ReaderDownloadAccessResponse>(`/library/me/books/${bookId}/download-access`, {
    token: options.token,
    query: { language: options.language ?? "en" },
  });
}

export function requestBookDownload(
  bookId: number,
  options: LibraryContextOptions & { language?: string },
) {
  return apiPost<BookDownloadPackageRead>(`/library/me/books/${bookId}/download`, undefined, {
    token: options.token,
    query: {
      language: options.language ?? "en",
      child_profile_id: options.childProfileId ?? undefined,
    },
  });
}

export async function downloadBookPackageForOffline(
  bookId: number,
  options: LibraryContextOptions & { language?: string },
): Promise<{ packageRecord: BookDownloadPackageRead; offlineRecord: OfflineBookPackageRecord }> {
  const packageRecord = await requestBookDownload(bookId, options);
  const payload = await fetchOfflinePackagePayload(packageRecord.package_url);
  const offlineRecord = await saveOfflineBookPackage({ packageRecord, payload });
  return { packageRecord, offlineRecord };
}
