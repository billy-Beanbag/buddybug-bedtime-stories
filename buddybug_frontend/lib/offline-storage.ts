"use client";

import { resolveApiUrl } from "@/lib/api";
import type {
  BookDownloadPackageRead,
  OfflineBookPackagePayload,
  OfflineBookPackageRecord,
  OfflineSyncActionRecord,
} from "@/lib/types";

const DATABASE_NAME = "buddybug-offline";
const DATABASE_VERSION = 1;
const OFFLINE_BOOK_STORE = "offline-books";
const SYNC_ACTION_STORE = "sync-actions";
const OFFLINE_RESOURCE_CACHE = "buddybug-offline-resources-v1";

function canUseIndexedDb() {
  return typeof window !== "undefined" && "indexedDB" in window;
}

function canUseCaches() {
  return typeof window !== "undefined" && "caches" in window;
}

function createOfflineBookKey(bookId: number, language: string) {
  return `${bookId}:${language}`;
}

function emitOfflinePackagesChanged() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("buddybug:offline-packages-changed"));
  }
}

function emitSyncQueueChanged() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("buddybug:sync-queue-changed"));
  }
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!canUseIndexedDb()) {
      reject(new Error("IndexedDB is not available in this browser"));
      return;
    }
    const request = window.indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onerror = () => reject(request.error || new Error("Unable to open offline storage"));
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(OFFLINE_BOOK_STORE)) {
        const store = database.createObjectStore(OFFLINE_BOOK_STORE, { keyPath: "key" });
        store.createIndex("book_id", "book_id", { unique: false });
      }
      if (!database.objectStoreNames.contains(SYNC_ACTION_STORE)) {
        database.createObjectStore(SYNC_ACTION_STORE, { keyPath: "id", autoIncrement: true });
      }
    };
    request.onsuccess = () => resolve(request.result);
  });
}

async function withStore<T>(
  storeName: string,
  mode: IDBTransactionMode,
  handler: (store: IDBObjectStore) => Promise<T> | T,
): Promise<T> {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(storeName, mode);
    const store = transaction.objectStore(storeName);
    Promise.resolve(handler(store))
      .then((result) => {
        transaction.oncomplete = () => {
          database.close();
          resolve(result);
        };
        transaction.onerror = () => {
          database.close();
          reject(transaction.error || new Error("Offline storage transaction failed"));
        };
        transaction.onabort = () => {
          database.close();
          reject(transaction.error || new Error("Offline storage transaction aborted"));
        };
      })
      .catch((error) => {
        database.close();
        reject(error);
      });
  });
}

function requestToPromise<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error("IndexedDB request failed"));
  });
}

async function cacheOfflineResourceUrls(urls: string[]) {
  if (!canUseCaches()) {
    return;
  }
  const cache = await window.caches.open(OFFLINE_RESOURCE_CACHE);
  const uniqueUrls = Array.from(new Set(urls.filter(Boolean).map((url) => resolveApiUrl(url))));
  await Promise.all(
    uniqueUrls.map(async (url) => {
      try {
        const response = await fetch(url, { credentials: "same-origin" });
        if (response.ok) {
          await cache.put(url, response.clone());
        }
      } catch {
        // Best-effort caching only.
      }
    }),
  );
}

export async function saveOfflineBookPackage(input: {
  packageRecord: BookDownloadPackageRead;
  payload: OfflineBookPackagePayload;
}): Promise<OfflineBookPackageRecord> {
  const now = new Date().toISOString();
  const record: OfflineBookPackageRecord = {
    key: createOfflineBookKey(input.payload.book.book_id, input.payload.language),
    book_id: input.payload.book.book_id,
    language: input.payload.language,
    title: input.payload.book.title,
    cover_image_url: input.payload.book.cover_image_url,
    age_band: input.payload.book.age_band,
    content_lane_key: input.payload.book.content_lane_key || null,
    package_version: input.payload.package_version,
    package_url: input.packageRecord.package_url,
    saved_at: now,
    updated_at: now,
    payload: input.payload,
  };

  await withStore(OFFLINE_BOOK_STORE, "readwrite", (store) => requestToPromise(store.put(record)));
  emitOfflinePackagesChanged();

  // Cache lightweight visual assets eagerly. Audio stays runtime-cached when it is actually played.
  await cacheOfflineResourceUrls([
    input.packageRecord.package_url,
    input.payload.book.cover_image_url || "",
    ...input.payload.pages.map((page) => page.image_url || ""),
  ]);

  return record;
}

export async function getOfflineBookPackage(
  bookId: number,
  language: string,
): Promise<OfflineBookPackageRecord | null> {
  const key = createOfflineBookKey(bookId, language);
  return withStore(OFFLINE_BOOK_STORE, "readonly", async (store) => {
    const result = await requestToPromise(store.get(key));
    return (result as OfflineBookPackageRecord | undefined) ?? null;
  });
}

export async function listOfflineBookPackages(): Promise<OfflineBookPackageRecord[]> {
  return withStore(OFFLINE_BOOK_STORE, "readonly", async (store) => {
    const result = await requestToPromise(store.getAll());
    return (result as OfflineBookPackageRecord[]).sort((left, right) =>
      right.updated_at.localeCompare(left.updated_at),
    );
  });
}

export async function removeOfflineBookPackage(bookId: number, language: string): Promise<void> {
  const key = createOfflineBookKey(bookId, language);
  await withStore(OFFLINE_BOOK_STORE, "readwrite", (store) => requestToPromise(store.delete(key)));
  emitOfflinePackagesChanged();
}

export async function markOfflineSyncAction(action: OfflineSyncActionRecord): Promise<number> {
  const id = await withStore(SYNC_ACTION_STORE, "readwrite", (store) =>
    requestToPromise(store.add(action)),
  );
  emitSyncQueueChanged();
  return Number(id);
}

export async function listPendingSyncActions(): Promise<OfflineSyncActionRecord[]> {
  return withStore(SYNC_ACTION_STORE, "readonly", async (store) => {
    const result = await requestToPromise(store.getAll());
    return (result as OfflineSyncActionRecord[]).sort((left, right) =>
      left.created_at.localeCompare(right.created_at),
    );
  });
}

export async function clearPendingSyncAction(id: number): Promise<void> {
  await withStore(SYNC_ACTION_STORE, "readwrite", (store) => requestToPromise(store.delete(id)));
  emitSyncQueueChanged();
}

export async function getPendingSyncActionCount(): Promise<number> {
  const actions = await listPendingSyncActions();
  return actions.length;
}

export async function fetchOfflinePackagePayload(packageUrl: string): Promise<OfflineBookPackagePayload> {
  const response = await fetch(resolveApiUrl(packageUrl), { credentials: "same-origin" });
  if (!response.ok) {
    throw new Error("Unable to fetch offline package");
  }
  return (await response.json()) as OfflineBookPackagePayload;
}
