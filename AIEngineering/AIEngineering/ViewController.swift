//
//  ViewController.swift
//  AIEngineering
//
//  Created by zhongqi yu on 2026/3/12.
//

import UIKit

// MARK: - View (Home)
final class ViewController: UIViewController {
    private let viewModel: HomeViewModel = HomeViewModel(service: MockHomeService())
    private var dataSource: [HomeItemViewData] = []

    private lazy var tableView: UITableView = {
        let tableView = UITableView(frame: .zero, style: .insetGrouped)
        tableView.translatesAutoresizingMaskIntoConstraints = false
        tableView.dataSource = self
        tableView.delegate = self
        tableView.register(UITableViewCell.self, forCellReuseIdentifier: "cell")
        return tableView
    }()

    private let refreshControl = UIRefreshControl()

    override func viewDidLoad() {
        super.viewDidLoad()

        title = "Home"
        view.backgroundColor = .systemBackground

        view.addSubview(tableView)
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        refreshControl.addTarget(self, action: #selector(onPullToRefresh), for: .valueChanged)
        tableView.refreshControl = refreshControl

        navigationItem.rightBarButtonItem = UIBarButtonItem(
            systemItem: .refresh,
            primaryAction: UIAction { [weak self] _ in
                self?.reload()
            }
        )

        bindViewModel()
        reload()
    }

    private func bindViewModel() {
        viewModel.onStateChange = { [weak self] state in
            guard let self else { return }
            switch state {
            case .idle:
                break
            case .loading:
                if !self.refreshControl.isRefreshing {
                    self.refreshControl.beginRefreshing()
                    self.tableView.setContentOffset(CGPoint(x: 0, y: -self.refreshControl.frame.height), animated: true)
                }
            case .loaded(let items):
                self.dataSource = items
                self.tableView.backgroundView = nil
                self.tableView.reloadData()
                self.refreshControl.endRefreshing()
            case .failed(let message):
                self.dataSource = []
                self.tableView.reloadData()
                self.refreshControl.endRefreshing()
                self.tableView.backgroundView = self.makeErrorView(message: message)
            }
        }
    }

    @objc private func onPullToRefresh() {
        reload()
    }

    private func reload() {
        Task { await viewModel.load() }
    }

    private func makeErrorView(message: String) -> UIView {
        let stack = UIStackView()
        stack.axis = .vertical
        stack.alignment = .center
        stack.spacing = 12

        let label = UILabel()
        label.text = message
        label.textAlignment = .center
        label.numberOfLines = 0
        label.textColor = .secondaryLabel

        let button = UIButton(type: .system)
        button.setTitle("Retry", for: .normal)
        button.addAction(UIAction { [weak self] _ in self?.reload() }, for: .touchUpInside)

        stack.addArrangedSubview(label)
        stack.addArrangedSubview(button)
        return stack
    }
}

extension ViewController: UITableViewDataSource, UITableViewDelegate {
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        dataSource.count
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "cell", for: indexPath)
        let item = dataSource[indexPath.row]
        var content = UIListContentConfiguration.subtitleCell()
        content.text = item.title
        content.secondaryText = item.subtitle
        cell.contentConfiguration = content
        cell.accessoryType = .disclosureIndicator
        return cell
    }

    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        let item = dataSource[indexPath.row]
        let alert = UIAlertController(title: item.title, message: item.subtitle, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }
}

// MARK: - ViewModel
@MainActor
final class HomeViewModel {
    enum State: Equatable {
        case idle
        case loading
        case loaded([HomeItemViewData])
        case failed(String)
    }

    var onStateChange: ((State) -> Void)?
    private(set) var state: State = .idle {
        didSet { onStateChange?(state) }
    }

    private let service: HomeServicing

    init(service: HomeServicing) {
        self.service = service
    }

    func load() async {
        state = .loading
        do {
            let items = try await service.fetchHomeItems()
            state = .loaded(items.map(HomeItemViewData.init))
        } catch {
            state = .failed("Load failed. \(error.localizedDescription)")
        }
    }
}

// MARK: - Model
struct HomeItem: Sendable, Equatable {
    let id: UUID
    let title: String
    let detail: String
}

struct HomeItemViewData: Equatable {
    let id: UUID
    let title: String
    let subtitle: String

    init(item: HomeItem) {
        self.id = item.id
        self.title = item.title
        self.subtitle = item.detail
    }
}

// MARK: - Service
protocol HomeServicing: Sendable {
    func fetchHomeItems() async throws -> [HomeItem]
}

enum HomeServiceError: Error {
    case simulatedFailure
}

struct MockHomeService: HomeServicing {
    func fetchHomeItems() async throws -> [HomeItem] {
        try await Task.sleep(nanoseconds: 700_000_000)

        if Bool.random() && Bool.random() {
            throw HomeServiceError.simulatedFailure
        }

        return [
            HomeItem(id: UUID(), title: "AI PR Learning", detail: "Learn from pull requests and summarize evidence."),
            HomeItem(id: UUID(), title: "GitHub Client", detail: "Fetch PRs and cache results."),
            HomeItem(id: UUID(), title: "Next Step", detail: "Replace MockHomeService with real API calls.")
        ]
    }
}
