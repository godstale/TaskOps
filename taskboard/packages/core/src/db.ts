import Database from 'better-sqlite3'

export type Db = Database.Database

/**
 * 기존 TaskOps DB 파일을 읽기 전용으로 연다.
 * 파일이 없으면 에러를 던진다.
 */
export function openDb(dbPath: string): Db {
  // readonly 옵션: DB를 수정하지 못하도록 강제
  return new Database(dbPath, { readonly: true })
}

export function closeDb(db: Db): void {
  db.close()
}
