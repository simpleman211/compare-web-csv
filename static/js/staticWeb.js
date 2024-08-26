// script.js

class FileUploader {
  constructor(inputId, listId) {
    this.fileInput = document.getElementById(inputId);
    this.fileList = document.getElementById(listId);
    this.init();
  }

  init() {
    this.fileInput.addEventListener("change", (event) =>
      this.handleFileChange(event)
    );
  }

  handleFileChange(event) {
    // this.fileList.innerHTML = ''; // Xóa danh sách cũ trước khi hiển thị danh sách mới

    // Lấy danh sách các tệp đã chọn
    const files = event.target.files;

    // Kiểm tra nếu có tệp nào được chọn
    if (files.length === 0) {
      return;
    }

    // Hiển thị tên tệp trong danh sách
    for (let j = 0; j < files.length; j++) {
      const div = document.createElement("div");
      const p = document.createElement("p");
      const i = document.createElement("i");

      div.classList.add("flex", "bg-slate-200", "mt-2", "mr-2");

      p.textContent = files[j].name;
      p.classList.add(
        "bg-slate-200",
        "p-2",
        "whitespace-nowrap",
        "overflow-hidden",
        "text-ellipsis",
        "w-40"
      );
      i.classList.add(
        "fa-solid",
        "fa-circle-xmark",
        "top-0",
        "justify-end",
        "hover:text-red-400",
        "cursor-pointer"
      );

      // Sự kiện xóa file không muốn upload
      i.addEventListener("click", function () {
        div.remove();
      });

      div.appendChild(p);
      div.appendChild(i);
      this.fileList.appendChild(div);
    }
  }
}

// Khởi tạo lớp FileUploader
document.addEventListener("DOMContentLoaded", () => {
  // Khởi tạo FileUploader cho form Process
  new FileUploader("uploadFileProcess", "fileListProcess");

  // Khởi tạo FileUploader cho form Compare
  new FileUploader("uploadFileCompare", "fileListCompare");
});
const downloadLink = document.getElementById("downloadLink");
const previewLink = document.getElementById("previewLink");
document.addEventListener("DOMContentLoaded", function () {
  if (downloadLink) {
    downloadLink.addEventListener("click", function () {
      setTimeout(() => {
        fetch("/cleanup")
          .then((response) => response.text())
          .then((data) => console.log(data))
          .catch((error) => console.error("Error:", error));
        downloadLink.remove();
        previewLink.remove();
      }, 1000);
    });
  }
});
function openPreview(containerName, blobName) {
  // Xây dựng URL để gọi API
  const url = `/preview/${containerName}/${blobName}`;

  // Gửi yêu cầu GET tới API để lấy nội dung của file
  fetch(url)
    .then((response) => response.text()) // Nhận dữ liệu dưới dạng văn bản
    .then((data) => {
      // Tách dữ liệu thành các phần tử tab và nội dung
      const parser = new DOMParser();
      const doc = parser.parseFromString(data, "text/html");

      // Tạo các tab buttons
      const tabButtons = doc.querySelectorAll("h3");
      const tabContents = doc.querySelectorAll("table");

      const tabContainer = document.querySelector(".tab");
      tabContainer.innerHTML = ""; // Xóa nội dung cũ nếu có

      tabButtons.forEach((button, index) => {
        const tabButton = document.createElement("button");
        tabButton.classList.add("tablinks");
        tabButton.setAttribute("data-tab", `tab${index + 1}`);
        tabButton.textContent = button.textContent;
        tabContainer.appendChild(tabButton);

        // Tạo các tab content
        const tabContent = document.createElement("div");
        tabContent.id = `tab${index + 1}`;
        tabContent.classList.add("tabcontent");
        tabContent.innerHTML = tabContents[index].outerHTML;
        document.getElementById("previewContent").appendChild(tabContent);
      });

      // Mở tab đầu tiên mặc định
      if (tabButtons.length > 0) {
        tabButtons[0].click();
      }

      // Hiển thị modal
      document.getElementById("previewBox").classList.remove("hidden");
    })
    .catch((error) => console.error("Error fetching preview:", error));
}

document.addEventListener("DOMContentLoaded", function () {
  const previewLink = document.getElementById("previewLink");
  const previewBox = document.getElementById("previewBox");
  const previewContent = document.getElementById("previewContent");
  const closePreview = document.getElementById("closePreview");
  const closePreviewBtn = document.getElementById("closePreviewBtn");
  const tabContainer = document.querySelector(".tab");
  let currentPage = 1;
  const rowsPerPage = 50; // Số dòng trên mỗi trang

  function paginateData(data, page) {
    const rows = data.trim().split("\n");
    const start = (page - 1) * rowsPerPage + 1; // Bỏ qua dòng tiêu đề
    const end = Math.min(page * rowsPerPage + 1, rows.length); // Bao gồm dòng tiêu đề
    return rows.slice(start, end);
  }

  function updatePreviewContent(data) {
    const rows = data.trim().split("\n");
    const header = rows[0].split(","); // Giả sử CSV sử dụng dấu phẩy
    const totalPages = Math.ceil((rows.length - 1) / rowsPerPage);
    previewContent.innerHTML = ""; // Xóa nội dung hiện tại

    // Tạo bảng
    const table = document.createElement("table");
    table.classList.add("w-full", "border-collapse");
    const thead = document.createElement("thead");
    const tbody = document.createElement("tbody");

    // Tạo tiêu đề bảng
    const headerRow = document.createElement("tr");
    header.forEach((headerText) => {
      const th = document.createElement("th");
      th.textContent = headerText;
      th.classList.add("border", "p-2", "bg-gray-200");
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Thêm các dòng phân trang vào bảng
    const paginatedRows = paginateData(data, currentPage);
    paginatedRows.forEach((rowData) => {
      const row = document.createElement("tr");
      const cells = rowData.split(",");
      cells.forEach((cellData) => {
        const cell = document.createElement("td");
        cell.textContent = cellData;
        cell.classList.add("border", "p-2");
        row.appendChild(cell);
      });
      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    previewContent.appendChild(table);

    // Tạo điều khiển phân trang
    const paginationControls = document.createElement("div");
    paginationControls.classList.add("pagination-controls");

    const maxPagesToShow = 10;
    const startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
    const endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);

    for (let i = startPage; i <= endPage; i++) {
      const pageLink = document.createElement("button");
      pageLink.textContent = i;
      pageLink.classList.add(
        "pagination-button",
        "mx-1",
        "px-2",
        "py-1",
        "border",
        "rounded"
      );
      if (i === currentPage) {
        pageLink.classList.add("bg-blue-500", "text-white");
      } else {
        pageLink.classList.add("bg-gray-200");
        pageLink.addEventListener("click", function () {
          currentPage = i;
          updatePreviewContent(data);
        });
      }
      paginationControls.appendChild(pageLink);
    }

    // Thêm điều khiển phân trang vào nội dung
    previewContent.appendChild(paginationControls);
  }

  if (previewLink) {
    previewLink.addEventListener("click", function (event) {
      event.preventDefault();
      const containerName = previewLink.getAttribute("data-container-name");
      const blobName = previewLink.getAttribute("data-blob-name");
      const url = `/preview/${containerName}/${blobName}`;

      fetch(url)
        .then((response) => response.text())
        .then((data) => {
          // Kiểm tra loại dữ liệu để quyết định cách xử lý
          if (blobName.toLowerCase().endsWith(".csv")) {
            // Hiển thị nội dung CSV
            updatePreviewContent(data);
          } else if (blobName.toLowerCase().endsWith(".xlsx")) {
            // Xử lý dữ liệu Excel
            const parser = new DOMParser();
            const doc = parser.parseFromString(data, "text/html");

            const sections = doc.querySelectorAll("h3");
            let tabHtml = '<div class="tab">';
            let contentHtml = "";
            const rowsPerPage = 50; // Số dòng trên mỗi trang
            const totalPagesPerTab = 10; // Tổng số trang tối đa

            sections.forEach((section, index) => {
              const sectionTitle = section.innerText;
              const sectionId = `sectionTab${index}`;

              tabHtml += `<button class="tablinks" data-tab="${sectionId}">${sectionTitle}</button>`;

              let sectionContent = "";
              let nextSibling = section.nextElementSibling;

              while (nextSibling && nextSibling.tagName !== "H3") {
                sectionContent += nextSibling.outerHTML;
                nextSibling = nextSibling.nextElementSibling;
              }

              if (sectionContent.trim() !== "") {
                // Chia nội dung thành các trang
                const parser = new DOMParser();
                const contentDoc = parser.parseFromString(
                  sectionContent,
                  "text/html"
                );
                const table = contentDoc.querySelector("table");
                const thead = table.querySelector("thead").outerHTML;
                const tbody = table.querySelector("tbody");
                const rows = Array.from(tbody.querySelectorAll("tr"));
                const totalPages = Math.ceil(rows.length / rowsPerPage);
                const totalTabs = Math.min(totalPages, totalPagesPerTab); // Giới hạn số trang tối đa trong mỗi tab
                let paginatedContent = "";

                for (let i = 0; i < totalTabs; i++) {
                  const pageRows = rows.slice(
                    i * rowsPerPage,
                    (i + 1) * rowsPerPage
                  );
                  const pageContent = `<table>${thead}<tbody>${pageRows
                    .map((row) => row.outerHTML)
                    .join("")}</tbody></table>`;
                  const pageId = `${sectionId}_page${i + 1}`;
                  paginatedContent += `<div id="${pageId}" class="tabcontent-page" style="display: ${
                    i === 0 ? "block" : "none"
                  };">${pageContent}</div>`;
                }

                // Thêm phân trang với các nút trang số
                let paginationButtons = "";
                for (let i = 1; i <= totalTabs; i++) {
                  paginationButtons += `<button class="page-number" data-section-id="${sectionId}" data-page="${i}">${i}</button>`;
                }

                contentHtml += `<div id="${sectionId}" class="tabcontent" style="display:none;">
                                                ${
                                                  section.outerHTML
                                                }${paginatedContent}
                                                <div class="pagination flex justify-center items-center" data-total-pages="${totalTabs}" data-current-page="1" data-section-id="${sectionId}">
                                                  <button class="prevPage" data-section-id="${sectionId}" ${
                  totalTabs <= 1 ? "disabled" : ""
                }></button>
                                                  ${paginationButtons}
                                                  <button class="nextPage" data-section-id="${sectionId}" ${
                  totalTabs <= 1 ? "disabled" : ""
                }></button>
                                                </div>
                                              </div>`;
              }

              console.log(
                `Tab ${index}:`,
                sectionTitle,
                sectionContent ? "-> Content exists" : "-> No content"
              );
            });

            tabHtml += "</div>";
            tabContainer.innerHTML = tabHtml + contentHtml;

            const firstTab = document.querySelector(".tablinks");
            if (firstTab) {
              firstTab.click();
            }
          } else {
            previewBox.innerHTML = "Unsupported file type";
          }

          previewBox.classList.remove("hidden");
        })
        .catch((error) => console.error("Error fetching preview:", error));
    });
  }

  const handleClosePreview = () => {
    previewBox.classList.add("hidden");
    sessionStorage.removeItem("showPreview");
  };

  if (closePreview || closePreviewBtn) {
    closePreview.addEventListener("click", handleClosePreview);
    closePreviewBtn.addEventListener("click", handleClosePreview);
  }

  document.addEventListener("click", function (evt) {
    if (evt.target.classList.contains("tablinks")) {
      document
        .querySelectorAll(".tabcontent")
        .forEach((content) => (content.style.display = "none"));
      document
        .querySelectorAll(".tablinks")
        .forEach((button) => button.classList.remove("active"));

      const tabId = evt.target.getAttribute("data-tab");
      document.getElementById(tabId).style.display = "block";
      evt.target.classList.add("active");
    }

    if (
      evt.target.classList.contains("prevPage") ||
      evt.target.classList.contains("nextPage")
    ) {
      const sectionId = evt.target.getAttribute("data-section-id");
      const pagination = document.querySelector(
        `.pagination[data-section-id="${sectionId}"]`
      );
      const currentPage = parseInt(
        pagination.getAttribute("data-current-page")
      );
      const totalPages = parseInt(pagination.getAttribute("data-total-pages"));
      let newPage = currentPage;

      if (evt.target.classList.contains("prevPage")) {
        newPage = Math.max(1, currentPage - 1);
      } else if (evt.target.classList.contains("nextPage")) {
        newPage = Math.min(totalPages, currentPage + 1);
      }

      if (newPage !== currentPage) {
        document.querySelector(
          `#${sectionId}_page${currentPage}`
        ).style.display = "none";
        document.querySelector(`#${sectionId}_page${newPage}`).style.display =
          "block";

        pagination.setAttribute("data-current-page", newPage);
        pagination.querySelector(
          ".pageInfo"
        ).innerText = `Page ${newPage} of ${totalPages}`;

        // Enable/disable buttons based on current page
        pagination.querySelector(".prevPage").disabled = newPage === 1;
        pagination.querySelector(".nextPage").disabled = newPage === totalPages;

        // Update page number buttons
        pagination.querySelectorAll(".page-number").forEach((button) => {
          button.classList.remove("active");
          if (parseInt(button.getAttribute("data-page")) === newPage) {
            button.classList.add("active");
          }
        });
      }
    }

    if (evt.target.classList.contains("page-number")) {
      const sectionId = evt.target.getAttribute("data-section-id");
      const pageNumber = parseInt(evt.target.getAttribute("data-page"));
      const pagination = document.querySelector(
        `.pagination[data-section-id="${sectionId}"]`
      );
      const currentPage = parseInt(
        pagination.getAttribute("data-current-page")
      );

      if (pageNumber !== currentPage) {
        document.querySelector(
          `#${sectionId}_page${currentPage}`
        ).style.display = "none";
        document.querySelector(
          `#${sectionId}_page${pageNumber}`
        ).style.display = "block";

        pagination.setAttribute("data-current-page", pageNumber);
        // pagination.querySelector(".pageInfo").innerText = `Page ${pageNumber} `;

        // Enable/disable buttons based on current page
        pagination.querySelector(".prevPage").disabled = pageNumber === 1;
        // pagination.querySelector(".nextPage").disabled = pageNumber === totalPages;

        // Update page number buttons
        pagination.querySelectorAll(".page-number").forEach((button) => {
          button.classList.remove("active");
          if (parseInt(button.getAttribute("data-page")) === pageNumber) {
            button.classList.add("active");
          }
        });
      }
    }
  });
});

// Tab for change between compare and process
document.addEventListener("DOMContentLoaded", function () {
  const tabProcess = document.getElementById("tabProcess");
  const tabCompare = document.getElementById("tabCompare");
  const tabContentProcess = document.getElementById("tabContentProcess");
  const tabContentCompare = document.getElementById("tabContentCompare");

  // Kiểm tra URL để xác định tab nào nên được kích hoạt
  const urlPath = window.location.pathname;

  if (urlPath === "/compare") {
    tabCompare.classList.add("active");
    tabProcess.classList.remove("active");
    tabContentCompare.classList.remove("hidden");
    tabContentProcess.classList.add("hidden");
  } else {
    tabProcess.classList.add("active");
    tabCompare.classList.remove("active");
    tabContentProcess.classList.remove("hidden");
    tabContentCompare.classList.add("hidden");
  }

  tabProcess.addEventListener("click", () => {
    tabProcess.classList.add("active");
    tabCompare.classList.remove("active");
    tabContentProcess.classList.remove("hidden");
    tabContentCompare.classList.add("hidden");
    // Thay đổi URL nếu cần
    window.history.pushState({}, "", "/process");
  });

  tabCompare.addEventListener("click", () => {
    tabCompare.classList.add("active");
    tabProcess.classList.remove("active");
    tabContentCompare.classList.remove("hidden");
    tabContentProcess.classList.add("hidden");
    // Thay đổi URL nếu cần
    window.history.pushState({}, "", "/compare");
  });
});
// Code alert noflications when no file in form
document.getElementById("processForm").addEventListener("submit", function(e) {
  const fileInput = document.getElementById("uploadFileProcess")

  if(fileInput.files.length === 0) {
    e.preventDefault();
    alert("Please select at least one file to process");
  }
})

document.getElementById("compareForm").addEventListener("submit", function(e) {
  const fileInput = document.getElementById("uploadFileCompare")

  if(fileInput.files.length === 0) {
    e.preventDefault();
    alert("Please select at least one file to compare");
  }
})